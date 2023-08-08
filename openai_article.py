from datetime import datetime, timedelta
import urllib.request
import os
from random import randint
from multiprocessing import Pool, Manager
from functools import partial
from openai_api import OpenAI_API
from wp_api import WP_API


class OpenAI_article(OpenAI_API, WP_API):
    def __init__(self, 
                api_key, 
                domain_name, 
                wp_login, 
                wp_pass,
                lang:str = None
                 ) -> None:
        
        self.total_tokens = 0

        OpenAI_API.__init__(self, api_key, lang)
        WP_API.__init__(self, domain_name, wp_login, wp_pass)


    def download_img(self, img_prompt, img_path):
        urllib.request.urlretrieve(self.create_img(img_prompt), img_path)
        return img_path
        

    def shift_date(self) -> datetime:
        self.publish_date['t'] += timedelta(days=self.days_delta) if self.forward_delta else -timedelta(days=self.days_delta)
        return self.publish_date['t']


    def create_article(self, 
                       header_num:int, 
                       title:str, 
                       cat_id:int = 1,
                       parallel:bool = False
                       ) -> (str, int):
        headers, img_prompt = self.create_headers(title,header_num)
        text = ""

        if parallel:
            data = [(title, h) for h in headers]
            with Pool() as pool:
                for header, p in pool.starmap(self.write_paragraph, data):
                    print(f"\t\tWrote section - {header}")
                    text += '<h2>'+header+'</h2>'+p
        else:
            for i, h in enumerate(headers):
                if h != '':
                    print(f"{cat_id}. {title}\t{i+1}/{header_num}: {h}")
                    header, p = self.write_paragraph(h, title)
                    text += '<h2>'+header+'</h2>'+p
                    i -= 1
        
        desc = self.write_description(text)
        if img_prompt != "":
            img = self.download_img(img_prompt, f".imgs/test_photo{datetime.now().microsecond}.webp")
            
            img_id = self.upload_img(img)
            os.remove(img)

            print(self.post_article(title, text, desc, img_id, self.shift_date(), cat_id)['link'])
        else:
            print("No img prompt - TARAPATAS!!")
            print(self.post_article(title, text, desc, "1", self.shift_date(), cat_id)['link'])

        print(f"Total tokens used: {self.total_tokens}")
        return title, cat_id
    

    def new_category(self, cat:str, parent_id:int = None) -> int:
        cat_desc = self.write_cat_description(cat)
        cat_json = self.create_category(cat, cat_desc, parent_id)
        cat_id = cat_json['id']
        return cat, int(cat_id)


    def create_structure(self, 
                         topic:str, 
                         category_num:int, 
                         subcategory_num:int
                         ):
        #create categories according to site topic
        categories = self.create_categories(topic, category_num)
        print(f"Created categories: {categories}")

        with Pool() as pool:
            #paralelly for each category create description & subcategories
            for cat, cat_id in pool.imap(self.new_category, categories):
                subcats = self.create_subcategories(cat, subcategory_num)
                print(f"Created subcategories: {subcats} for category {cat}")
                scats = [(c, cat_id) for c in subcats]
                for scat, scat_id in pool.starmap(self.new_category, scats):
                    print(f"Adding articles to subcategory {scat_id}: {scat} scat_json['link']")
                    

    def populate_structure(self, 
                         article_num:int, 
                         header_num:int,
                         start_date: datetime = datetime.now(), 
                         days_delta:int = 7, 
                         forward_delta:bool = True
                         ):
        #set publication time & delay parameters
        self.publish_date = Manager().dict()
        self.publish_date['t'] = start_date
        self.days_delta = days_delta
        self.forward_delta = forward_delta
        #get categories from WP API
        categories = self.get_categories()
        #create data tuple for each category
        data_prime = [(c['name'], article_num, c['id']) for c in categories if c['name'] != "Bez kategorii"]

        #for small articles parallelize writing articles
        if article_num > header_num:
            with Pool() as pool:
                for titles, cat_id in pool.starmap(self.create_titles, data_prime):
                    data = [(header_num, t, cat_id) for t in titles]
                    pool.starmap(self.create_article, data)
        #for big articles parallelize writing sections
        else:
            for d in data_prime:
                titles, cat_id = self.create_titles(*d)
                for t in titles:
                    self.create_article(header_num, t, cat_id, parallel=True)


if __name__ == "__main__":
    pass