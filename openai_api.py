import openai
import time
from random import randint
from multiprocessing import Pool
from functools import partial


class OpenAI_API:
    def __init__(self, 
                 api_key,
                 lang:str = None
                 ) -> None:
        
        openai.api_key = api_key
        self.total_tokens = 0 
        self.model = "gpt-3.5-turbo"

        self.lang = lang

        self.langs = {
            "pl": "",
            "de": " Odpowiedz w języku Niemieckim - Reply in German language.",
            "en": " Odpowiedz w języku Angielskim - Reply in English language.",
            "cs": " Odpowiedz w języku Czeskim - Reply in Czech language.",
            "sk": " Odpowiedz w języku Słowackim - Reply in Slovak language."
        }


    def ask_openai(self, system:str, user:str) -> dict:
        prompt = [
            {"role": "system", "content": system + self.lang_prompt()},
            {"role": "user", "content": user}
        ]
        time.sleep(randint(0,2))

        while True:
            try:
                response = openai.ChatCompletion.create(model=self.model, messages=prompt)
            except openai.error.RateLimitError:
                print("Too many requests, waiting 30s and trying again")
                time.sleep(30)
                continue
            except Exception as e:
                print("Unknown error, waiting & resuming")
                print(e)
                time.sleep(3)
                continue
            break

        self.total_tokens += response["usage"]["total_tokens"]

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

    
    def create_categories(self, topic, category_num = 5) -> list[str]:
        system = "Give most precise answer without explanation nor context. List your answear line by line. Don't use quotemarks."
        user = f'Przygotuj {category_num} nazw kategorii o dla strony blogowej o tematyce {topic}, każda z nazw kategorii powinna być powiązana z {topic}, podaj tylko nazwy kategorii. Każda nazwa kategorii powinna mieć od 1 do 3 słów.'

        response = self.ask_openai(system, user)
        
        return self.cleanup_category(response['choices'][0]['message']['content'])


    def create_subcategories(self, category, topic, subcategory_num = 5) -> list[str]:
        system =  f"Jesteś ekspertem w temacie {category} i musisz w krótki i precyzyjny sposób przedstawić informacje."
        user = f'Przygotuj {subcategory_num} nazw podkategorii (o długości od 1 do 4 słów) dla kategorii {category} o tematyce {topic} podaj tylko nazwy podkategorii. Każda nazwa podkategorii powinna mieć długość od 1 do 4 słów.'

        response = self.ask_openai(system, user)

        return [i[i.find(" ")+1:] for i in response['choices'][0]['message']['content'].split('\n')]
    

    def write_cat_description(self, text:str) -> str:        
        system = "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."
        user = f'Napisz opis kategorii o nazwie {text} o długości maksymalnie 2 paragrafów'

        response = self.ask_openai(system, user)

        return response['choices'][0]['message']['content']
    

    def cleanup_titles(self, text, num) -> list[str]:
        titles = text.split('\n')
        titles = [t.strip() for t in titles if t]
        titles = titles[:num]
        titles = [t[t.find(". ")+1:].replace("\"","").replace("\'","") for t in titles]
        return titles        
    

    def create_titles(self, topic:str, article_num:int = 5, cat_id:int = 1) -> tuple[list[str], int]:
        system =  "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."
        user = f'Przygotuj {str(article_num)+" tytułów artykułów" if article_num>1 else "tytuł artykułu"} o tematyce {topic} podaj tylko tytuły'
            
        response = self.ask_openai(system, user)

        return self.cleanup_titles(response['choices'][0]['message']['content'], article_num), cat_id
    

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


    def create_headers(self, title:str, header_num:int = 5) -> tuple[list[str], int]:
        system = "Give most precise answer without explanation nor context. List your answear line by line. Don't use quotemarks"
        user = f'Wylistuj {header_num} nagłówków dla artykułu skupionego na tematyce {title} oraz na końcu krótki opis zdjęcia, które pasowałoby do całości artykułu. Nie używaj cudzysłowów.' 
        
        response = self.ask_openai(system, user)
        
        header_prompts, img_prompt = self.cleanup_header(response['choices'][0]['message']['content'], header_num)

        return header_prompts, img_prompt
    

    def write_paragraph(self, title:str, header:str, keyword:str = "", url:str  = "", nofollow:int = 0) -> tuple[str,str]:
        if (keyword!="" and url!=""):
            return self.write_paragraph_linked(title, header, keyword, url, nofollow)
        system =  "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."
        user = f'Napisz fragment artykułu o tematyce {title} skupiający się na aspekcie {header}. Artykuł powinien być zoptymalizowany pod słowa kluczowe dotyczące tego tematu. Artykuł powinien zawierać informacje na temat. Tekst umieść w <p></p>.'
        
        time.sleep(randint(0,3))
        response = self.ask_openai(system, user)

        return header, response['choices'][0]['message']['content']
    

    def write_paragraph_linked(self, title:str, header:str, keyword:str, url:str, nofollow:int = 0) -> tuple[str,str]:
        system =  "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."
        user = f"Napisz fragment artykułu o tematyce {title} skupiający się na aspekcie {header} powiązany z frazą {keyword}. W treści powinien znaleźć się jeden link HTML w postaci „<a href=\"{url}\">{keyword}</a>” do podstrony {url}, anchorem tego linku powinna być fraza kluczowa (może być odmieniona, może być zmieniona kolejność wyrazów, może zostać użyty synonim). Treść wynikowa powinna być gotowym kodem HTML zawierającym m.in. takie znaczniki jak <p>, <a> itp."
        
        response = self.ask_openai(system, user)

        text = response['choices'][0]['message']['content']

        chance = randint(0,100)
        nf = ""
        if int(nofollow) > chance:
            nf = " rel=\"nofollow\""
            start = text.find("<a")
            end = start + text[start:].find(">")
            text = text[:end] + nf + text[end:]

        if text.find("<a href=\"{url}\">{keyword}</a>") > 0:
            return header, text
        elif text.find("<a href=\"{url}\"") > 0:
            #swap the keword
            start = text.find("<a href=\"{url}\"")
            start += text[start:].find(">")
            end = start + text[start:].find("</a>")
            return header, text[:start+1]+keyword+text[end:]
        elif text.find("<a"):
            #swap link&keyword
            start = text.find("<a")
            end = start + text[start:].find("</a>")
            return header, text[:start+2] + f" href=\"{url}\"{nf}>{keyword}" + text[end:]
        else:
            #generate again
            return self.write_paragraph_linked(title, header, keyword, url, nofollow)


    def write_description(self, text:str) -> str:
        system =  "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem. Napisz tylko jeden paragraf"
        reduced_text = " ".join(text.split()[:500]) if len(text.split()) > 500 else text
        user = f'Dla poniższego artykułu napisz 4 zdania = jeden paragraf, podsumowujących jego treść i zachęcający czytelnika do przeczytania całości artykułu:\n{reduced_text}'
        
        response = self.ask_openai(system, user)

        return response['choices'][0]['message']['content']
    

    def create_img(self, img_prompt) -> str:
        helper = "Na zdjęciu znajdują się tylko przedmioty, ewentualnie martwa natura. "
        try:
            response = openai.Image.create(
                prompt=helper+img_prompt,
                n=1,
                size="512x512"
            )
        except openai.error.InvalidRequestError:
            img_prompt = self.ask_openai("Jesteś redaktorem treści na portalu dla dzieci", "Przebuduj to zdanie tak, aby było family friendly - "+img_prompt)
            response = openai.Image.create(
                prompt=helper+img_prompt['choices'][0]['message']['content'],
                n=1,
                size="512x512"
            )
        image_url = response['data'][0]['url']
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
