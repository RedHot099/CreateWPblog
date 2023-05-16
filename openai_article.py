import openai
import requests
import time
import json
import base64
from datetime import datetime, timedelta
import urllib.request
import os


class OpenAI_article:
    def __init__(self, api_key, 
                 domain_name, 
                 wp_login, 
                 wp_pass
                 ) -> None:
        
        openai.api_key = api_key
        self.total_tokens = 0 
        self.model = "gpt-3.5-turbo"
        
        self.url = f"https://{domain_name}/wp-json/wp/v2"
        wp_credentials = wp_login + ":" + wp_pass
        self.wp_token = base64.b64encode(wp_credentials.encode())

    
    def create_categories(self, topic, category_num = 5):
        prompt = [
            {"role": "system", "content": f"Jesteś ekspertem w temacie {topic} i musisz w krótki i precyzyjny sposób przedstawić informacje."},
            {"role": "user", "content": f'Przygotuj {category_num} nazw kategorii o tematyce {topic} podaj tylko nazwy kategorii. Każda nazwa kategorii powinna mieć od 1 do 3 słów.'}
        ]

        while True:
            try:
                response = openai.ChatCompletion.create(model=self.model, messages=prompt)
            except openai.error.RateLimitError:
                print("Too many requests, waiting 30s and trying again")
                time.sleep(30)
                continue
            break
        self.total_tokens += response["usage"]["total_tokens"]
        return [i[i.find(" ")+1:] for i in response['choices'][0]['message']['content'].split('\n')]


    def create_subcategories(self, category, subcategory_num = 5):
        prompt = [
            {"role": "system", "content": f"Jesteś ekspertem w temacie {category} i musisz w krótki i precyzyjny sposób przedstawić informacje."},
            {"role": "user", "content": f'Przygotuj {subcategory_num} nazw podkategorii dla kategorii {category} o tematyce podaj tylko nazwy podkategorii. Każda nazwa podkategorii powinna mieć od 3 do 5x słów.'}
        ]

        while True:
            try:
                response = openai.ChatCompletion.create(model=self.model, messages=prompt)
            except openai.error.RateLimitError:
                print("Too many requests, waiting 30s and trying again")
                time.sleep(30)
                continue
            break
        self.total_tokens += response["usage"]["total_tokens"]
        return [i[i.find(" ")+1:] for i in response['choices'][0]['message']['content'].split('\n')]
    

    def write_cat_description(self, text:str) -> str:        
        prompt = [
            {"role": "system", "content": "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."},
            {"role": "user", "content": f'Napisz opis kategorii o nazwie {text}'}
        ]

        while True:
            try:
                desc_reponse = openai.ChatCompletion.create(model=self.model, messages=prompt, max_tokens=200)
            except openai.error.RateLimitError:
                print("Too many requests, waiting 30s and trying again")
                time.sleep(30)
                continue
            break
        self.total_tokens += desc_reponse["usage"]["total_tokens"]

        return desc_reponse['choices'][0]['message']['content']
    

    def create_titles(self, topic:str, article_num:int = 5):
        prompt = [
            {"role": "system", "content": "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."},
            {"role": "user", "content": f'Przygotuj {str(article_num)+" tytułów artykułów" if article_num>1 else "tytuł artykułu"} o tematyce {topic} podaj tylko tytuły'}
        ]

        while True:
            try:
                topic_response = openai.ChatCompletion.create(model=self.model, messages=prompt)
            except openai.error.RateLimitError:
                print("Too many requests, waiting 30s and trying again")
                time.sleep(30)
                continue
            break
        self.total_tokens += topic_response["usage"]["total_tokens"]
        return [i[i.replace(")",".").find(". ")+1 if i.find(".") else i.find("\"")+1:].replace("\"", "") for i in topic_response['choices'][0]['message']['content'].split('\n')]
    

    def create_headers(self, title:str, header_num:int = 5):
        prompt = [
            {"role": "system", "content": "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."},
            {"role": "user", "content": f'Wylistuj {header_num} nagłówków dla artykułu skupionego na tematyce {title} oraz na końcu krótki opis zdjęcia, które pasowałoby do całości artykułu'}
        ]

        while True:
            try:
                headers_response = openai.ChatCompletion.create(model=self.model, messages=prompt)
            except openai.error.RateLimitError:
                print("Too many requests, waiting 30s and trying again")
                time.sleep(30)
                continue
            break
        self.total_tokens += headers_response["usage"]["total_tokens"]
        
        img_prompt = headers_response['choices'][0]['message']['content'].split('\n')[-1].split(":")[-1]

        header_prompts = [h[h.replace(")",".").find(". ")+1:].replace("\"", "") for h in headers_response['choices'][0]['message']['content'].split('\n')[:-2]]

        return header_prompts, img_prompt
    

    def write_paragraph(self, header:str, title:str):
        prompt = [
            {"role": "system", "content": "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."},
            {"role": "user", "content": f'Napisz fragment artykułu o tematyce {title} skupiający się na aspekcie {header}. Artykuł powinien być zoptymalizowany pod słowa kluczowe dotyczące tego tematu. Artykuł powinien zawierać informacje na temat. Tekst umieść w <p></p>.'}
        ]

        while True:
            try:
                p_response = openai.ChatCompletion.create(model=self.model, messages=prompt)
            except openai.error.RateLimitError:
                print("Too many requests, waiting 30s and trying again")
                time.sleep(30)
                continue
            break
        self.total_tokens += p_response["usage"]["total_tokens"]

        p = p_response['choices'][0]['message']['content']

        return p

    def write_description(self, text:str) -> str:
        prompt = [
            {"role": "system", "content": "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."},
            {"role": "user", "content": f'Dla poniższego artykułu napisz dłuższy paragraf podsumowujący jego treść i zachęcający czytelnika do przeczytania całości artykułu:\n{text}'}
        ]

        while True:
            try:
                desc_reponse = openai.ChatCompletion.create(model=self.model, messages=prompt, max_tokens=200)
            except openai.error.RateLimitError:
                print("Too many requests, waiting 30s and trying again")
                time.sleep(30)
                continue
            break
        self.total_tokens += desc_reponse["usage"]["total_tokens"]

        return desc_reponse['choices'][0]['message']['content']
    

    def create_img(self, img_prompt):
        response = openai.Image.create(
            prompt=img_prompt,
            n=1,
            size="512x512"
        )
        image_url = response['data'][0]['url']
        # self.total_tokens += response["usage"]["total_tokens"]
        return image_url
    

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
        for i, h in enumerate(headers):
            if h != '':
                print(f"\t\t{i+1}/{header_num}: {h}")
                p = self.write_paragraph(h, title)
                text += '<h2>'+h+'</h2>'+p
                i -= 1
        
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
                         days_delta:int = 7, 
                         forward_delta:bool = True, 
                         cat_id:int = 1
                         ):

        print(f"Creating {article_num} articles on topic {topic} - each containg {header_num} sub-sections")
        titles = self.create_titles(topic, article_num)

        publish_date = datetime.now()
        
        for i, title in enumerate(titles):
            print(f"Article {i+1}/{article_num}: {title}")
            self.create_article(header_num, title, publish_date, cat_id)

            publish_date = publish_date + timedelta(days=days_delta) if forward_delta else publish_date - timedelta(days=days_delta)


    def create_structure(self, 
                         topic:str, 
                         category_num:int, 
                         subcategory_num:int, 
                         article_num:int, 
                         header_num:int, 
                         days_delta:int = 7, 
                         forward_delta:bool = True
                         ):
        
        categories = self.create_categories(topic, category_num)
        print(f"Created categories: {categories}")

        for cat in categories:
            cat_desc = self.write_cat_description(cat)
            cat_json = self.create_category(cat, cat_desc)
            cat_id = cat_json['id']
            print(f"Created category {cat_id}: {cat_json['link']}")

            self.publish_articles(cat, article_num, header_num, days_delta, forward_delta, cat_id)
            subcats = self.create_subcategories(cat, subcategory_num)
            print(f"Created subcategories: {subcats}")
            for scat in subcats:
                scat_desc = self.write_cat_description(scat)
                scat_json = self.create_category(scat, scat_desc, cat_id)
                scat_id = scat_json['id']
                print(f"Created subcategory {scat_id}: {scat_json['link']}")

                self.publish_articles(scat, article_num, header_num, days_delta, forward_delta, scat_id)




    def create_category(self, name:str, desc:str, parent_id:int = None):
        header = {'Authorization': 'Basic ' + self.wp_token.decode('utf-8')}

        post = {
            "name": name, 
            "description": desc,
            "parent": parent_id
        }

        response = requests.post(self.url+"/categories", headers=header, json=post)
        try:
            response.json()['id']
        except:
            return self.get_category_id(name)
        return response.json()
    

    def get_category_id(self, category_name):
        categories_endpoint = f'{self.url}/categories?per_page=100'

        header = {'Authorization': 'Basic ' + self.wp_token.decode('utf-8')}

        response = requests.get(categories_endpoint, headers=header)
        categories = response.json()

        for category in categories:
            if category['name'] == category_name:
                return {'id': category['id'], 'link': category['link']}
    
    
    def upload_img(self, img):
        header = {"Content-Disposition": f"attachment; filename=\"post_photo.webp\"",
          "Content-Type": "image/webp",
          'Authorization': 'Basic ' + self.wp_token.decode('utf-8')
          }

        data = open(img, 'rb').read()

        response = requests.post(url=self.url+"/media",data=data,headers=header)

        return response.json()['id']
    

    def post_article(self, 
                     title:str, 
                     text:str, 
                     desc:str, 
                     img_id:int, 
                     date:datetime, 
                     categories:int = 1,
                     author_id:int = 1, 
                     comment_status:bool = False
                     ):
        
        header = {'Authorization': 'Basic ' + self.wp_token.decode('utf-8')}

        post = {
        'title'         : title,
        'content'       : text,
        'excerpt'       : desc,
        'author'        : author_id,
        'categories'    : categories,
        'featured_media': img_id,
        'status'        : 'publish' if(date <= datetime.now()) else 'future',
        'date'          : date.strftime("%Y-%m-%d %H:%M:%S"),
        'comment_status' : "open" if comment_status else "closed"
        }

        response = requests.post(self.url+"/posts", headers=header, json=post)
        return response.json()



if __name__ == "__main__":
    pass
