from datetime import datetime, timedelta
import urllib.request
import os
from random import randint
from multiprocessing import Pool
from functools import partial
from openai_api import OpenAI_API
from wp_api import WP_API


class OpenAI_article(OpenAI_API, WP_API):
    def __init__(self) -> None:
        self.total_tokens = 0

    def download_img(self, img_prompt, img_path):
        urllib.request.urlretrieve(self.create_img(img_prompt), img_path)
        return img_path


    def create_article(self, 
                       header_num:int, 
                       title:str, 
                       publish_date: datetime, 
                       cat_id:int = 1
                       ):
        headers, img_prompt = self.create_headers(title,header_num)
        text = ""
        print("\tWriting sub-sections")
        func = partial(self.write_paragraph, title)
        with Pool() as pool:
            for header, p in pool.imap(func, headers):
                print(f"\t\tWrote section - {header}")
                text += '<h2>'+header+'</h2>'+p

        # for i, h in enumerate(headers):
        #     if h != '':
        #         print(f"\t\t{i+1}/{header_num}: {h}")
        #         p = self.write_paragraph(h, title)
        #         text += '<h2>'+h+'</h2>'+p
        #         i -= 1
        
        print(f"\tCreating article description")
        desc = self.write_description(text)
        
        print(f"\tCreateing image: {img_prompt}")
        if img_prompt != "":
            img = self.download_img(img_prompt, ".imgs/test_photo.webp")
            
            img_id = self.upload_img(img)
            os.remove(img)

        print("\tUploading article")
        print(self.post_article(title, text, desc, img_id, publish_date, cat_id)['link'])

        print(f"Total tokens used: {self.total_tokens}")


    def publish_articles(self, 
                         topic:str, 
                         article_num:int, 
                         header_num:int, 
                         start_date: datetime, 
                         days_delta:int = 7, 
                         forward_delta:bool = True, 
                         cat_id:int = 1
                         ):

        print(f"Creating {article_num} articles on topic {topic} - each containg {header_num} sub-sections")
        titles = self.create_titles(topic, article_num)
        
        for i, title in enumerate(titles):
            print(f"Article {i+1}/{article_num}: {title}")
            self.create_article(header_num, title, start_date, cat_id)

            start_date = start_date + timedelta(days=days_delta) if forward_delta else start_date - timedelta(days=days_delta)

        return start_date


    def create_structure(self, 
                         topic:str, 
                         category_num:int, 
                         subcategory_num:int, 
                         article_num:int, 
                         header_num:int, 
                         days_delta:int = 7, 
                         forward_delta:bool = True
                         ):
        
        start_date = datetime.now()
        categories = self.create_categories(topic, category_num)
        print(f"Created categories: {categories}")

        for cat in categories:
            cat_desc = self.write_cat_description(cat)
            cat_json = self.create_category(cat, cat_desc)
            cat_id = cat_json['id']
            print(f"Adding articles to category {cat_id}: {cat_json['link']}")

            start_date = self.publish_articles(cat, article_num, header_num, start_date, days_delta, forward_delta, cat_id)
            subcats = self.create_subcategories(cat, subcategory_num)
            print(f"Created subcategories: {subcats}")
            for scat in subcats:
                scat_desc = self.write_cat_description(scat)
                scat_json = self.create_category(scat, scat_desc, cat_id)
                scat_id = scat_json['id']
                print(f"Adding articles to subcategory {scat_id}: {scat_json['link']}")

                start_date = self.publish_articles(scat, article_num, header_num, start_date, days_delta, forward_delta, scat_id)



if __name__ == "__main__":
    pass
