import requests
import base64
from datetime import datetime
from random import randint
import json

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WP_API:
    def __init__(self,
                 domain_name,
                 wp_login,
                 wp_pass
                 ) -> None:
        
        
        self.url = f"https://{domain_name}/wp-json/wp/v2"
        wp_credentials = wp_login + ":" + wp_pass
        self.wp_token = base64.b64encode(wp_credentials.encode())
        self.validate_credentials()

    
    def get_post_count(self):
        header = {'Authorization': 'Basic ' + self.wp_token.decode('utf-8')}
        try:
            response = requests.get(self.url+"/posts?per_page=1", headers=header)
        except Exception as e:
            print(self.url+" - "+e)
            return 0

        if response.status_code == 200:
            return int(response.headers['x-wp-total'])


    def get_category_count(self):
        header = {'Authorization': 'Basic ' + self.wp_token.decode('utf-8')}
        try:
            response = requests.get(self.url+"/categories?per_page=1", headers=header)
        except Exception as e:
            print(self.url+" - "+e)
            return 0

        if response.status_code == 200:
            return int(response.headers['x-wp-total'])


    def validate_credentials(self):
        header = {'Authorization': 'Basic ' + self.wp_token.decode('utf-8')}
        try:
            response = requests.get(self.url+'/posts?per_page=1', headers=header)
        except Exception as e:
            print(self.url)
            print(e)
            raise Exception(e)

        if response.status_code == 200:
            return 0
        else:
            print(self.url)
            print(response.json())
            raise Exception("Invalid Wordpress credentials")


    def create_category(self, name:str, desc:str, parent_id:int = None) -> dict:
        header = {'Authorization': 'Basic ' + self.wp_token.decode('utf-8')}

        post = {
            "name": name, 
            "description": desc,
            "parent": parent_id
        }

        response = requests.post(self.url+"/categories", headers=header, json=post, verify = False)
        try:
            # print(f"Created category with ID - {response.json()['id']} - {response.json()['link']}")
            response.json()['id']
        except:
            return self.get_category_id(name)
        return response.json()
    

    def get_categories(self, num:int = 100) -> dict:
        categories_endpoint = f'{self.url}/categories?per_page={num}'
        header = {'Authorization': 'Basic ' + self.wp_token.decode('utf-8')}

        response = requests.get(categories_endpoint, headers=header, verify = False)
        return response.json()
    

    def get_category_id(self, category_name) -> dict:
        categories = self.get_categories()
        for category in categories:
            if category['name'].lower() == category_name.lower():
                print(f"Category {category['name']} exists with ID - {category['id']} - {category['link']}")
                return {'id': category['id'], 'link': category['link']}
            
        print(f"Category {category_name} not really exists")
        return {'id': 0, 'link': 'no_cat'}
    
    
    def upload_img(self, img) -> int:
        header = {"Content-Disposition": f"attachment; filename=\"post_photo.webp\"",
          "Content-Type": "image/webp",
          'Authorization': 'Basic ' + self.wp_token.decode('utf-8')
          }

        data = open(img, 'rb').read()

        response = requests.post(url=self.url+"/media",data=data,headers=header, verify = False)

        try:
            return response.json()['id']
        except:
            print("Problem while uploading image", response.json())
            return None
    

    def post_article(self, 
                     title:str, 
                     text:str, 
                     desc:str, 
                     img_id:int, 
                     date:datetime, 
                     categories:int = 1,
                     author_id:int = 1, 
                     comment_status:bool = False
                     ) -> dict:
        
        header = {'Authorization': 'Basic ' + self.wp_token.decode('utf-8')}

        #if only date passed roll dice for hour, minutes and seconds
        if date.hour == 0:
            date = date.replace(hour=randint(1, 23), minute=randint(1, 59), second=randint(1, 59))

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

        response = requests.post(self.url+"/posts", headers=header, json=post, verify = False)
        return response.json()
    



if __name__ == "__main__":
    pass