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
                       ) -> tuple[str, int]:
        headers, img_prompt = self.create_headers(title,header_num)
        text = ""

        if links:
            links = links + [{'keyword':'', 'url':''}]*(len(headers) - len(links))
            data = [(title, h, d['keyword'], d['url'], nofollow) for d, h in zip(links, headers)]
        else:
            data = [(title, h) for h in headers]


        if parallel:
            with Pool() as pool_p:
                for header, p in pool_p.starmap(self.write_paragraph, data):
                    print(f"\t\tWrote section - {header}")
                    text += '<h2>'+header+'</h2>'+p
                pool_p.close()
                pool_p.join()
        else:
            for d in data:
                print(f"{cat_id}\t{d}")
                header, p = self.write_paragraph(*d)
                text += '<h2>'+header+'</h2>'+p
        
        desc = self.write_description(text)
        if img_prompt != "":
            img = self.download_img(img_prompt, f"{path}.imgs/test_photo{datetime.now().microsecond}.webp")
            
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
        print(f"Total tokens used: {self.total_tokens}")
        return (response, cat_id)
    

    def new_category(self, cat:str, parent_id:int = None) -> int:
        cat_desc = self.write_cat_description(cat)
        cat_json = self.create_category(cat, cat_desc, parent_id)
        return cat, cat_json


    def create_structure(self, 
                         topic:str, 
                         category_num:int, 
                         subcategory_num:int
                         ) -> dict:
        #create categories according to site topic
        categories = self.create_categories(topic, category_num)
        print(f"Created categories: {categories}")
        structure = {}

        with Pool() as pool_cat:
            #paralelly for each category create description & subcategories
            for cat, cat_json in pool_cat.imap(self.new_category, categories):
                subcats = self.create_subcategories(cat, topic, subcategory_num)
                print(f"Created subcategories: {subcats} for category {cat} - {cat_json['link']}")
                structure[cat] = subcats
                scats = [(c, cat_json['id']) for c in subcats]
                with Pool() as pool_scat:
                    pool_scat.starmap(self.new_category, scats)
                    pool_scat.close()
                    pool_scat.join()
            pool_cat.close()
            pool_cat.join()

        return structure
                    

    def populate_structure(self, 
                         article_num:int, 
                         header_num:int,
                         categories:list[dict] | str = [],
                         path:str = "",
                         links:list[dict] = [],
                         nofollow:int = 0
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

        if 1:
            with Pool() as pool_titles:
                for titles, cat_id in pool_titles.starmap(self.create_titles, data_prime):
                    self.titles.append((titles, cat_id))
                pool_titles.close()
                pool_titles.join()
        else:
            for d in data_prime:
                self.titles.append(self.create_titles(*d))

        #output dict
        urls = {}
        print("Article tites - ", self.titles)
        #for small articles parallelize writing articles
        if article_num > header_num:
            with Pool() as pool_h:
                for titles, cat_id in self.titles:
                    data = [(header_num, t, cat_id, False, path, links, nofollow) for t in titles]
                    for res, id in pool_h.starmap(self.create_article, data):
                        id = int(id)
                        if id in urls.keys():
                            urls[id].append(res)
                        else:
                            urls[id] = [res]
                pool_h.close()
                pool_h.join()
        #for big articles parallelize writing sections
        else:
            for titles, cat_id in self.titles:
                print(str(cat_id)+" - writing articles: \n - " + "\n - ".join(titles))
                for t in titles:
                    res, id = self.create_article(header_num, t, cat_id, parallel=True, path=path, links=links, nofollow=nofollow)
                    id = int(id)
                    if id in urls.keys():
                        urls[id].append(res)
                    else:
                        urls[id] = [res]

        print(urls)
        return urls


if __name__ == "__main__":
    pass