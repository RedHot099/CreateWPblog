import time
from random import randint
from multiprocessing import Pool
from functools import partial

import openai
from openai import OpenAI, AsyncOpenAI
import asyncio
import httpx
import re


class OpenAI_API:
    def __init__(self, 
                 api_key,
                 lang:str = None,
                 text_model = "gpt-3.5-turbo-1106",
                 image_model = "dall-e-3"
                 ) -> None:
        # os.environ["OPENAI_API_KEY"] = api_key
        self.api_key = api_key
        self.text_model = text_model
        self.image_model = image_model
        self.total_tokens = 0 

        self.lang = lang

        self.client = AsyncOpenAI(
            api_key=self.api_key
            )

        self.langs = {
            "pl": " Odpowiedz w języku Polskim - Reply in Polish language.",
            "de": " Odpowiedz w języku Niemieckim - Reply in German language.",
            "en": " Odpowiedz w języku Angielskim - Reply in English language.",
            "cs": " Odpowiedz w języku Czeskim - Reply in Czech language.",
            "sk": " Odpowiedz w języku Słowackim - Reply in Slovak language.",
            "fr": " Odpowiedz w języku Francuskim - Reply in French language.",
            "es": " Odpowiedz w języku Hiszpańskim - Reply in Spanish language.",
            "ro": " Odpowiedz w języku Rumuńskim - Reply in Romanian language."
        }


    async def ask_openai(self, system:str, user:str, timeout:float = 80.0) -> dict:
        prompt = [
            {"role": "system", "content": system + self.lang_prompt()},
            {"role": "user", "content": user}
        ]
        time.sleep(randint(0,2))

        while True:
            try:
                response = await self.client.with_options(timeout=timeout).chat.completions.create(model=self.text_model, messages=prompt)
            except openai.RateLimitError:
                print("Too many requests, waiting 30s and trying again")
                time.sleep(30)
                continue
            except openai.APITimeoutError:
                print("OpenAI timeout - ", timeout)
            except openai.APIStatusError as e:
                print("Unknown error, waiting & resuming - ", e.status_code, e.response)
                time.sleep(3)
                continue
            except openai.APIConnectionError as e:
                print("The server could not be reached")
                print(e.__cause__)  # an underlying Exception, likely raised within httpx.
                time.sleep(3)
                continue
            except openai.APIError as e:
                print("Unknown error, waiting & resuming - ", e)
                time.sleep(3)
                continue
            except httpx.TimeoutException as e:
                print("HTTPX timeout error, waiting & resuming - ", timeout)
                time.sleep(3)
                continue
            break

        return response
    

    def lang_prompt(self) -> str:
        if self.lang in self.langs.keys():
            return self.langs[self.lang]
        else:
            return ""

    def get_langs(self) -> list[str]:
        return self.langs.keys()
        

    def cleanup_category(self, text) -> list[str]:
        text = text.replace("\'","")
        text = text.replace("\"","")
        text = text.replace(")","")
        cats = text.split('\n')
        if len(cats) == 1: cats = text.split(",")
        cats = [c[c.find(". ")+2:].title() if c.find(". ")>0 else c.title() for c in cats]
        return cats

    
    def create_categories(self, topic:str, category_num:int = 5) -> tuple[list[str], int]:
        system = "Give most precise answer without explanation nor context. List your answear line by line. Don't use quotemarks."
        user = f'Przygotuj {category_num} nazw kategorii o dla strony blogowej o tematyce {topic}, każda z nazw kategorii powinna być powiązana z {topic}, podaj tylko nazwy kategorii. Każda nazwa kategorii powinna mieć od 1 do 3 słów.'

        response = self.ask_openai(system, user, category_num*2.0)
        
        return self.cleanup_category(response['choices'][0]['message']['content']), int(response["usage"]["total_tokens"])


    def create_subcategories(self, category, topic, subcategory_num = 5) -> tuple[list[str], int]:
        system =  f"Jesteś ekspertem w temacie {category} i musisz w krótki i precyzyjny sposób przedstawić informacje. Give most precise answer without explanation nor context. List your answear line by line. Don't use quotemarks."
        user = f'Przygotuj {subcategory_num} nazw podkategorii (o długości od 1 do 4 słów) dla kategorii {category} o tematyce {topic} podaj tylko nazwy podkategorii. Każda nazwa podkategorii powinna mieć długość od 1 do 4 słów.'

        response = self.ask_openai(system, user)

        return [i[i.find(" ")+1:] for i in response['choices'][0]['message']['content'].split('\n')], int(response["usage"]["total_tokens"])
    

    def write_cat_description(self, text:str) -> tuple[str, int]:        
        system = "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."
        user = f'Napisz opis kategorii o nazwie {text} o długości maksymalnie 2 paragrafów'

        response = self.ask_openai(system, user)

        return response['choices'][0]['message']['content'], int(response["usage"]["total_tokens"])
    

    def cleanup_titles(self, text, num) -> list[str]:
        titles = text.split('\n')
        titles = [t.strip() for t in titles if t]
        titles = titles[:num]
        titles = [t[t.find(". ")+1:].replace("\"","").replace("\'","").strip() for t in titles]
        return titles        
    

    async def create_titles(self, topic:str, article_num:int = 5, cat_id:int = 1) -> tuple[list[str], int, int]:
        system = "Give most precise answer without explanation nor context. List your answear line by line. Don't use quotemarks."
        user = f'Przygotuj {str(article_num)+" tytułów artykułów" if article_num>1 else "tytuł artykułu"} o tematyce {topic} podaj tylko tytuły'
            
        response = await self.ask_openai(system, user, article_num*8.0)

        return self.cleanup_titles(response.choices[0].message.content, article_num), cat_id, int(response.usage.total_tokens)
    

    def cleanup_header(self, text, header_num) -> tuple[list[str], int]:
        #cleanup text
        text = text.replace("\"","")
        #get img prompt from last line of text
        img = text.split('\n')[-1]
        #get headers text from first n lines
        headers = text.split('\n')
        headers = [h for h in headers if h]
        headers = headers[:header_num]
        #remove numeration from headers
        headers = [h[h.find(". ")+1:].strip() for h in headers]
        return headers, img


    async def create_headers(self, title:str, header_num:int = 5) -> tuple[list[str], str, int]:
        system = "Give most precise answer without explanation nor context. List your answear line by line. Don't use quotemarks"
        user = f'Wylistuj {header_num} nagłówków dla artykułu skupionego na tematyce {title} oraz na końcu krótki opis zdjęcia, które pasowałoby do całości artykułu. Nie używaj cudzysłowów.' 
        
        response = await self.ask_openai(system, user, header_num*10.0)
        
        header_prompts, img_prompt = self.cleanup_header(response.choices[0].message.content, header_num)

        return header_prompts, img_prompt, int(response.usage.total_tokens)
    

    def remove_non_p_tags(self, text):
        text = text.replace("<article>", "")
        text = text.replace("</article>", "")
        text = text.replace("<article>", "")
        text = text.replace("</article>", "")
        text = re.sub(r'<h1\b[^>]*>.*?</h1>', '', text, flags=re.DOTALL)
        text = re.sub(r'<h2\b[^>]*>.*?</h2>', '', text, flags=re.DOTALL)
        return text
    

    async def write_paragraph(self, title:str, header:str, keyword:str = "", url:str  = "", nofollow:int = 0) -> tuple[str, str, int]:
        if (keyword!="" and url!=""):
            linked_response = await self.write_paragraph_linked(title, header, keyword, url, nofollow)
            return linked_response
        system =  "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."
        user = f'Napisz fragment artykułu o tematyce {title} skupiający się na aspekcie {header}. Artykuł powinien być zoptymalizowany pod słowa kluczowe dotyczące tego tematu. Artykuł powinien zawierać informacje na temat. Tekst umieść w <p></p>. Unikaj używania tagu <article>'
        
        time.sleep(randint(0,3))
        response = await self.ask_openai(system, user, 50.0)

        return header, self.remove_non_p_tags(response.choices[0].message.content), int(response.usage.total_tokens)
    

    async def write_paragraph_linked(self, title:str, header:str, keyword:str, url:str, nofollow:int = 0) -> tuple[str, str, int]:
        if not url.startswith("http"):
            url = "https://"+url
        system =  "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."
        user = f"Napisz fragment artykułu o tematyce {title} skupiający się na aspekcie {header} powiązany z frazą {keyword}. W treści powinien znaleźć się jeden link HTML w postaci „<a href=\"{url}\">{keyword}</a>” do podstrony {url}, anchorem tego linku powinna być fraza kluczowa (może być odmieniona, może być zmieniona kolejność wyrazów, może zostać użyty synonim). Tekst umieść w <p></p>."
        
        response = await self.ask_openai(system, user)

        text = self.remove_non_p_tags(response.choices[0].message.content)

        chance = randint(0,100)
        nf = ""
        if int(nofollow) > chance:
            nf = " rel=\"nofollow\""
            start = text.find("<a ")
            end = start + text[start:].find(">")
            text = text[:end] + nf + text[end:]

        if text.find(f"<a href=\"{url}\">{keyword}</a>") > 0:
            return header, text, int(response.usage.total_tokens)
        elif text.find(f"<a href=\"{url}\"") > 0:
            #swap the keword
            base = text.find(f"<a href=\"{url}\"")
            start = base + text[base:].find(">")
            end = start + text[start:].find("</a")
            print("Wrong keyword in ahref - ", text[base:end+4])
            print(keyword)
            return header, text[:start+1]+keyword+text[end:], int(response.usage.total_tokens)
        elif text.find("<a ") > 0:
            #swap link&keyword
            start = text.find("<a ")
            end = start + text[start:].find("</a")
            print("Wrong link in anhor", text[start:end+4], start, end)
            print(url, keyword)
            return header, text[:start+2] + " href=\""+url+"\""+nf+">"+keyword + text[end:], int(response.usage.total_tokens)
        else:
            #generate again
            return await self.write_paragraph_linked(title, header, keyword, url, nofollow)


    async def write_description(self, text:str) -> tuple[str, int]:
        system =  "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem. Napisz tylko jeden paragraf"
        reduced_text = " ".join(text.split()[:500]) if len(text.split()) > 500 else text
        user = f'Dla poniższego artykułu napisz 4 zdania = jeden paragraf, podsumowujących jego treść i zachęcający czytelnika do przeczytania całości artykułu:\n{reduced_text}'
        
        response = await self.ask_openai(system, user, 40.0)

        return response.choices[0].message.content, int(response.usage.total_tokens)
    

    def create_img(self, img_prompt) -> str:
        client = OpenAI(api_key=self.api_key)
        helper = "Na zdjęciu znajdują się tylko przedmioty, ewentualnie martwa natura. "
        response = client.images.generate(
            model=self.image_model,
            prompt=helper+img_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        return image_url
    
    def create_favicon(self, topic) -> str:
        response = openai.Image.create(
            prompt=f"simple abstract favicon logo with no text for blog about {topic}, cool grid pattern, very small 64x64 logo, pixel art, gradient, simetric, centered, balanced",
            n=1,
            size="256x256"
        )
        image_url = response['data'][0]['url']
        return image_url
    


if __name__ == "__main__":
    pass
