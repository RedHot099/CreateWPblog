from datetime import datetime, timedelta
import urllib.request
import os
import json
from random import randint, shuffle
from multiprocessing import Pool, Manager
from .openai_api import OpenAI_API
from .wp_api import WP_API


class OpenAI_article(OpenAI_API, WP_API):
    def __init__(self, 
                api_key, 
                domain_name, 
                wp_login, 
                wp_pass,
                lang:str = None, 
                start_date: datetime = datetime.now(),
                days_delta:int = 7, 
                forward_delta:bool = True
                ) -> None:
        
        self.total_tokens = 0
        #set publication time & delay parameters
        manager = Manager()
        self.publish_date = manager.dict()
        self.publish_date['t'] = start_date
        self.titles = manager.list()

        self.days_delta = days_delta
        self.forward_delta = forward_delta

        OpenAI_API.__init__(self, api_key, lang)
        WP_API.__init__(self, domain_name, wp_login, wp_pass)


    def download_img(self, img_prompt, img_path) -> str:
        urllib.request.urlretrieve(self.create_img(img_prompt), img_path)
        return img_path
        

    def shift_date(self) -> datetime:
        self.publish_date['t'] += timedelta(days=self.days_delta) if self.forward_delta else -timedelta(days=self.days_delta)
        return self.publish_date['t']


    def create_article(self, 
                       header_num:int, 
                       title:str, 
                       cat_id:int = 1,
                       parallel:bool = False,
                       path:str = '',
                       links:list[dict] = None,
                       nofollow:int = 0
                       ) -> tuple[str, int, int]:
        headers, img_prompt, tokens = self.create_headers(title,header_num)
        text = ""

        if links[0]['keyword'] == '' and links[0]['url'] == '':
            print("No links in links")
            data = [(title, h) for h in headers]
        elif links:
            links = links + [{'keyword':'', 'url':''}]*(len(headers) - len(links))
            data = [(title, h, d['keyword'], d['url'], nofollow) for d, h in zip(links, headers)]
        else:
            data = [(title, h) for h in headers]


        if parallel:
            with Pool() as pool_p:
                for header, p, t in pool_p.starmap(self.write_paragraph, data):
                    print(f"{cat_id}\t{header}")
                    text += '<h2>'+header+'</h2>'+p
                    tokens += t
                pool_p.close()
                pool_p.join()
        else:
            for i, d in enumerate(data):
                print(f"{i+1}/{len(data)}: {d}")
                header, p, t = self.write_paragraph(*d)
                text += '<h2>'+header+'</h2>'+p
                tokens += t
        
        desc, t = self.write_description(text)
        tokens += t
        if img_prompt != "":
            img = self.download_img(img_prompt, f"{path}files/test_photo{datetime.now().microsecond}.webp")
            
            img_id = self.upload_img(img)
            os.remove(img)
        else:
            print("No img prompt - TARAPATAS!!")
            img_id = None

        if img_id:
            print('uploading article')
            response = self.post_article(title, text, desc, img_id, self.publish_date['t'], cat_id)['link']
        else:
            print('no image id - uploading with default image')
            response = self.post_article(title, text, desc, "1", self.publish_date['t'], cat_id)['link']

        print(response)
        self.shift_date()
        print(f"Total tokens used: {tokens}")
        return response, cat_id, tokens
    

    def new_category(self, cat:str, parent_id:int = None) -> tuple[int, dict, int]:
        cat_desc, tokens = self.write_cat_description(cat)
        cat_json = self.create_category(cat, cat_desc, parent_id)
        return cat, cat_json, tokens


    def create_structure(self, 
                         topic:str, 
                         category_num:int, 
                         subcategory_num:int
                         ) -> dict:
        #create categories according to site topic
        categories, tokens = self.create_categories(topic, category_num)
        print(f"Created categories: {categories}")
        structure = {}

        with Pool() as pool_cat:
            #paralelly for each category create description & subcategories
            for cat, cat_json, t in pool_cat.imap(self.new_category, categories):
                tokens += t
                subcats, subc_t = self.create_subcategories(cat, topic, subcategory_num)
                tokens += subc_t
                print(f"Created subcategories: {subcats} for category {cat} - {cat_json['link']}")
                structure[cat] = subcats
                scats = [(c, cat_json['id']) for c in subcats]
                with Pool() as pool_scat:
                    pool_scat.starmap(self.new_category, scats)
                    pool_scat.close()
                    pool_scat.join()
            pool_cat.close()
            pool_cat.join()

        return structure, tokens
                    

    def populate_structure(self, 
                         article_num:int, 
                         header_num:int,
                         categories:list[dict] = [],
                         path:str = "",
                         links:list[dict] = [],
                         nofollow:int = 0, 
                         topic:str = ""
                         ) -> dict:
        #if no categories get categories from WP API
        if categories == []:
            categories = self.get_categories()
        elif type(categories)==str:
            categories = json.loads(categories)
        #parse json data
        if type(links)==str:
            links = json.loads(links)
        #create data tuple for each category
        data_prime = [(c['name'], article_num, int(c['id'])) for c in categories if c['name'] != "Bez kategorii"]
        if len(data_prime) == 0:
            data_prime = [(topic, article_num, 1)]

        tokens = 0
        while len(self.titles) < len(categories):
            if len(data_prime) > 1:
                with Pool() as pool_titles:
                    for titles, cat_id, t in pool_titles.starmap(self.create_titles, data_prime):
                        tokens += t
                        for title in titles:
                            self.titles.append((title, cat_id))
                    pool_titles.close()
                    pool_titles.join()
            else:
                for d in data_prime:
                    titles, cat_id, t = self.create_titles(*d)
                    tokens += t
                    for title in titles:
                        self.titles.append((title, cat_id))

        #output dict
        urls = {}
        self.titles = self.titles[:len(categories)*article_num]
        links += [{'keyword':'', 'url':''}]*(len(self.titles) - len(links))
        print("Article tites - ", len(self.titles), ":")
        for t, id in self.titles:
            print(id, t)
        #for small articles parallelize writing articles
        if article_num*len(self.titles) > header_num:
            with Pool() as pool_h:
                data = [(header_num, t, cat_id, False, path, [link], nofollow) for ((t, cat_id), link) in zip(self.titles, links)]
                for res, id, t in pool_h.starmap(self.create_article, data):
                    tokens += t
                    id = int(id)
                    if id in urls.keys():
                        urls[id].append(res)
                    else:
                        urls[id] = [res]
                pool_h.close()
                pool_h.join()
        #for big articles parallelize writing sections
        else:
            for i, ((title, cat_id), link) in enumerate(zip(self.titles,links)):
                print(f"{i+1}/{len(self.titles)}: {title}")
                res, id, t = self.create_article(header_num, title, cat_id, parallel=True, path=path, links=[link], nofollow=nofollow)
                tokens += t
                id = int(id)
                if id in urls.keys():
                    urls[id].append(res)
                else:
                    urls[id] = [res]

        return urls, tokens


if __name__ == "__main__":
    pass