from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO
from itertools import zip_longest
import requests
import os
import json
import asyncio
from multiprocessing import Pool, Manager
from .openai_api import OpenAI_API
from .wp_api import WP_API


class OpenAI_article(OpenAI_API, WP_API):
    def __init__(self, 
                api_key:str, 
                domain_name:str, 
                wp_login:str, 
                wp_pass:str,
                lang:str = None, 
                start_date:datetime = datetime.now(),
                days_delta:int = 7, 
                forward_delta:bool = True
                ) -> None:
        
        self.total_tokens = 0
        #set publication time & delay parameters
        manager = Manager()
        self.publish_date = manager.dict()
        self.publish_date['t'] = start_date
        self.titles = manager.list()
        self.domain = domain_name

        self.days_delta = days_delta
        self.forward_delta = forward_delta

        OpenAI_API.__init__(self, api_key, lang)
        WP_API.__init__(self, domain_name, wp_login, wp_pass)


    def get_domain(self):
        return self.domain  


    async def download_img(self, img_prompt, img_path) -> str:
        image = Image.open(BytesIO(requests.get(await self.create_img(img_prompt)).content))
        # image = image.resize((1200, 628)).convert('RGB')
        image.save(img_path, format='WEBP')

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
                if len(data) > 1:
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
            response = self.post_article(title, text, desc, img_id, self.publish_date['t'], cat_id)['link']
        else:
            print('no image id - uploading with default image')
            response = self.post_article(title, text, desc, "1", self.publish_date['t'], cat_id)['link']

        print("Uploaded article - ", response)
        self.shift_date()
        return response, cat_id, tokens
    

    async def new_category(self, cat:str, parent_id:int = None) -> tuple[int, dict, int]:
        cat_desc, tokens = await self.write_cat_description(cat)
        cat_json = self.create_category(cat, cat_desc, parent_id)
        return cat, cat_json["id"], tokens


    async def create_substructure(self, 
                                  topic: str,
                                  subcategory_num: int,
                                  category_name: str, 
                                  cat_id: int,
                                  ):
        total_tokens = 0
        subcategories, tokens = await self.create_subcategories(category_name, topic, subcategory_num)
        total_tokens += tokens

        subcategories_tasks = []
        for subcateogory in subcategories:
            subcategories_tasks.append(asyncio.create_task(self.new_category(subcateogory, cat_id)))
        
        created_subcategories = await asyncio.gather(*subcategories_tasks)

        for _, _, tokens in created_subcategories:
            total_tokens += tokens

        return category_name, subcategories, total_tokens

        
        
        
    
    async def create_structure(self, 
                         topic:str, 
                         category_num:int, 
                         subcategory_num:int
                         ) -> dict:
        total_tokens = 0
        #create categories according to site topic
        categories, tokens = await self.create_categories(topic, int(category_num))
        total_tokens += tokens
        structure = {}

        categories_tasks = []
        subcategories_tasks = []
        for category in categories:
            categories_tasks.append(asyncio.create_task(self.new_category(category)))

        created_categories = await asyncio.gather(*categories_tasks)
        for category, cat_id, tokens in created_categories:
            subcategories_tasks.append(asyncio.create_task(self.create_substructure(topic, subcategory_num, category, cat_id)))
            total_tokens += tokens

        subcategories = await asyncio.gather(*subcategories_tasks)
        for c, s, tokens in subcategories:
            total_tokens += tokens
            structure[c] = s

        return structure, total_tokens
                    

    def populate_structure(self, 
                         article_num:int, 
                         header_num:int,
                         categories:list[dict] = [],
                         path:str = "",
                         links:list[dict] = [],
                         nofollow:int = 0, 
                         topic:str = ""
                         ) -> tuple[dict,int, str]:
        #if no categories get categories from WP API
        if categories == []:
            categories = self.get_categories()
        elif type(categories)==str:
            categories = json.loads(categories)
        #parse json data
        if type(links)==str:
            links = json.loads(links)
        elif links is None:
            links = []
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

        return urls, tokens, self.domain
    

    async def write_article(self, 
                            title:str, 
                            header_num:int, 
                            cat_id:int = 1,
                            path:str = '',
                            links:list[dict] = None,
                            nofollow:int = 0
                            ) -> tuple[str, int, int]:
        
        #generate headers & promt for generating image
        print("Creating headers for - ", title)
        headers, img_prompt, headers_tokens = await self.create_headers(title,header_num)
        
        p_tasks = []
        #write paragraphs with links first
        if links:
            for l, h in zip(links, headers[:len(links)]):
                p_tasks.append(asyncio.create_task(self.write_paragraph(title, h, l['keyword'], l['url'], nofollow)))
        #queue up rest of paragraphs
        for h in headers:
            p_tasks.append(asyncio.create_task(self.write_paragraph(title, h)))
        print("Writing paragraphs for article - ", title)
        paragraphs = await asyncio.gather(*p_tasks)
        #merge all texts into single string article
        text = ""
        for header, paragraph, tokens in paragraphs:
            text += "<h2>"+header+"</h2>"
            text += paragraph

        #Write description
        desc, tokens = await self.write_description(text)

        #Generate & download image
        if img_prompt != "":
            img = await self.download_img(img_prompt, f"{path}files/test_photo{datetime.now().microsecond}.webp")
            #Upload image to WordPress
            img_id = self.upload_img(img)
            #Delete local image
            os.remove(img)
        else:
            print("No img prompt - TARAPATAS!!")
            img = await self.download_img(
                f"Create image for article titled - {title}", 
                f"{path}files/test_photo{datetime.now().microsecond}.webp")
            #Upload image to WordPress
            img_id = self.upload_img(img)
            #Delete local image
            os.remove(img)
        
        #Upload article to Wordpress
        if img_id:
            response = self.post_article(title, text, desc, img_id, self.publish_date['t'], cat_id)['link']
        else:
            print('no image id - uploading with default image')
            response = self.post_article(title, text, desc, "1", self.publish_date['t'], cat_id)['link']


        print("Uploaded article - ", response)
        self.shift_date()
        return response, cat_id, tokens
    
    
    async def main(self, 
                    article_num:int, 
                    header_num:int,
                    categories:list[dict] = [],
                    path:str = "",
                    links:list[dict] = [],
                    nofollow:int = 0, 
                    topic:str = ""):
        
        '''
        GOTO data structure
        [
            {
                "cat": "",
                "articles": [
                    {
                        "title": "",
                        "headers": [], 
                        "paragraphs": [] 
                    }
                ], 
                ...articles
            },
            ...categories
        ]
        '''
        
        titles_tasks = []
        for category in categories:
            titles_tasks.append(asyncio.create_task(self.create_titles(category['name'],article_num,category['id'])))

        titles_list = await asyncio.gather(*titles_tasks)

        try:
            json.loads(links)
        except:
            links = []
        articles_tasks = []
        for titles, cat_id, tokens in titles_list:
            for title in titles:
                articles_tasks.append(asyncio.create_task(self.write_article(title, header_num, cat_id, path, [links.pop()] if links else None, nofollow)))

        res = await asyncio.gather(*articles_tasks)

        return res


if __name__ == "__main__":
    pass