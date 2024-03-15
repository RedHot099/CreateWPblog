from random import randint

import openai
from openai import OpenAI, AsyncOpenAI
from types import SimpleNamespace
import httpx
import re
import inspect
import asyncio


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
        self.models_cost = {
            "dall-e-3": 0.040, 
            "dall-e-2": 0.020,
            "gpt-3.5-turbo-1106": [0.0010/1000, 0.0020/1000], 
            "gpt-4": [0.03/1000, 0.06/1000],
            "gpt-4-32k": [0.06/1000, 0.12/1000]
        }

        self.lang = lang

        self.client = AsyncOpenAI(
            api_key=self.api_key
            )

        self.timeout_multiplier = 1
        self.base_sleep = 3

        self.langs = {
            "pl": " Odpowiedz w języku Polskim - Reply in Polish language.",
            "de": " Odpowiedz w języku Niemieckim - Reply in German language.",
            "en": " Odpowiedz w języku Angielskim - Reply in English language.",
            "au": " Odpowiedz w języku Angielskim - Reply in English language.",
            "cs": " Odpowiedz w języku Czeskim - Reply in Czech language.",
            "sk": " Odpowiedz w języku Słowackim - Reply in Slovak language.",
            "fr": " Odpowiedz w języku Francuskim - Reply in French language.",
            "es": " Odpowiedz w języku Hiszpańskim - Reply in Spanish language.",
            "nl": " Odpowiedz w języku Niderlandzkim - Reply in Dutch language.",
            "ro": " Odpowiedz w języku Rumuńskim - Reply in Romanian language.",
            "sv": " Odpowiedz w języku Szwedzkim - Reply in Swedish language."
        }


    async def ask_openai(self, system:str, user:str, timeout:float = 80.0) -> dict:
        prompt = [
            {"role": "system", "content": system + self.lang_prompt()},
            {"role": "user", "content": user}
        ]
        await asyncio.sleep(randint(0,2))

        response = SimpleNamespace(**{"choices": [SimpleNamespace(**{"message": SimpleNamespace(**{"content": ""})})]})

        while not response.choices[0].message.content:
            try:
                response = await self.client.with_options(timeout=timeout*self.timeout_multiplier).chat.completions.create(model=self.text_model, messages=prompt)
            except openai.AuthenticationError:
                print("Wrong api key!")
                raise Exception("Wrong API key")
            except openai.RateLimitError:
                print("Too many requests, waiting {}s and trying again".format(self.base_sleep*10))
                await asyncio.sleep(self.base_sleep * 10)
                self.base_sleep += 2
                continue
            except openai.APITimeoutError:
                print("OpenAI timeout - ", timeout)
                self.timeout_multiplier *= 1.5
            except openai.APIStatusError as e:
                print("Unknown error, waiting & resuming - ", e.status_code, e.response)
                await asyncio.sleep(self.base_sleep)
                self.base_sleep += 1
                continue
            except openai.APIConnectionError as e:
                print("The server could not be reached")
                print(e.__cause__)
                await asyncio.sleep(self.base_sleep)
                self.base_sleep += 1
                continue
            except openai.APIError as e:
                print("Unknown error, waiting & resuming - ", e)
                await asyncio.sleep(self.base_sleep)
                self.base_sleep += 1
                continue
            except httpx.TimeoutException as e:
                print("HTTPX timeout error, waiting & resuming - ", timeout)
                self.timeout_multiplier *= 1.2
                await asyncio.sleep(self.base_sleep)
                continue
            except RuntimeError as e:
                print("Runtime Error")
                print(inspect.stack())
                continue
            finally:
                if self.base_sleep > 111:
                    raise Exception("Too many OpenAI API timeouts - please try again later")

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

    
    async def create_categories(self, topic:str, category_num:int = 5) -> tuple[list[str], int, float]:
        system = "Give most precise answer without explanation nor context. List your answear line by line. Don't use quotemarks."
        user = f'Przygotuj {category_num} nazw kategorii o dla strony blogowej o tematyce {topic}, każda z nazw kategorii powinna być powiązana z {topic}, podaj tylko nazwy kategorii. Każda nazwa kategorii powinna mieć od 1 do 3 słów.'

        response = await self.ask_openai(system, user, category_num*2.0)
        
        return self.cleanup_category(response.choices[0].message.content), int(response.usage.total_tokens), float(int(response.usage.total_tokens)*self.models_cost[self.text_model][1])


    async def create_subcategories(self, category, topic, subcategory_num = 5) -> tuple[list[str], int, float]:
        system =  f"Jesteś ekspertem w temacie {category} i musisz w krótki i precyzyjny sposób przedstawić informacje. Give most precise answer without explanation nor context. List your answear line by line. Don't use quotemarks."
        user = f'Przygotuj {subcategory_num} nazw podkategorii (o długości od 1 do 4 słów) dla kategorii {category} o tematyce {topic} podaj tylko nazwy podkategorii. Każda nazwa podkategorii powinna mieć długość od 1 do 4 słów.'

        response = await self.ask_openai(system, user)

        return [i[i.find(" ")+1:] for i in response.choices[0].message.content.split('\n')], int(response.usage.total_tokens), float(int(response.usage.total_tokens)*self.models_cost[self.text_model][1])
    

    async def write_cat_description(self, text:str) -> tuple[str, int, float]:        
        system = "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."
        user = f'Napisz opis kategorii o nazwie {text} o długości maksymalnie 2 paragrafów'

        response = await self.ask_openai(system, user, 150.0)

        return response.choices[0].message.content, int(response.usage.total_tokens), float(int(response.usage.total_tokens)*self.models_cost[self.text_model][1])
    

    def cleanup_titles(self, text, num) -> list[str]:
        titles = text.split('\n')
        titles = [t.strip() for t in titles if t]
        titles = titles[:num]
        titles = [t[t.find(". ")+1:].replace("\"","").replace("\'","").strip() for t in titles]
        return titles        
    

    async def create_titles(self, topic:str, article_num:int = 5, cat_id:int = 1) -> tuple[list[str], int, int, float]:
        system = "Give most precise answer without explanation nor context. List your answear line by line. Don't use quotemarks."
        user = f'Przygotuj {str(article_num)+" tytułów artykułów" if article_num>1 else "tytuł artykułu"} o tematyce {topic} podaj tylko tytuły'
            
        response = await self.ask_openai(system, user, article_num*20.0)

        return self.cleanup_titles(response.choices[0].message.content, article_num), cat_id, int(response.usage.total_tokens), float(int(response.usage.total_tokens)*self.models_cost[self.text_model][1])
    

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


    async def create_headers(self, title:str, header_num:int = 5) -> tuple[list[str], str, int, float]:
        system = "Give most precise answer without explanation nor context. List your answear line by line. Don't use quotemarks"
        user = f'Wylistuj {header_num} nagłówków dla artykułu skupionego na tematyce {title} oraz na końcu krótki opis zdjęcia, które pasowałoby do całości artykułu. Nie używaj cudzysłowów.' 
        
        response = await self.ask_openai(system, user, header_num*120.0)
        
        header_prompts, img_prompt = self.cleanup_header(response.choices[0].message.content, header_num)

        return header_prompts, img_prompt, int(response.usage.total_tokens), float(int(response.usage.total_tokens)*self.models_cost[self.text_model][1])
    

    def remove_non_p_tags(self, text):
        text = text.replace("<article>", "")
        text = text.replace("</article>", "")
        text = text.replace("<article>", "")
        text = text.replace("</article>", "")
        text = re.sub(r'<h1\b[^>]*>.*?</h1>', '', text, flags=re.DOTALL)
        text = re.sub(r'<h2\b[^>]*>.*?</h2>', '', text, flags=re.DOTALL)
        return text
    

    async def write_paragraph(self, title:str, header:str, keyword:str = "", url:str  = "", nofollow:int = 0) -> tuple[str, str, int, float]:
        if (keyword!="" and url!=""):
            linked_response = await self.write_paragraph_linked(title, header, keyword, url, nofollow)
            return linked_response
        system =  "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."
        user = f'Napisz fragment artykułu o tematyce {title} skupiający się na aspekcie {header}. Artykuł powinien być zoptymalizowany pod słowa kluczowe dotyczące tego tematu. Artykuł powinien zawierać informacje na temat. Tekst umieść w <p></p>. Unikaj używania tagu <article>'
        
        await asyncio.sleep(randint(0,3))
        response = await self.ask_openai(system, user, 180.0)

        return header, self.remove_non_p_tags(response.choices[0].message.content), int(response.usage.total_tokens), float(int(response.usage.total_tokens)*self.models_cost[self.text_model][1])
    

    async def write_paragraph_linked(self, title:str, header:str, keyword:str, url:str, nofollow:int = 0) -> tuple[str, str, int, float]:
        if not url.startswith("http"):
            url = "https://"+url
        system =  "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem."
        user = f"Napisz fragment artykułu o tematyce {title} skupiający się na aspekcie {header} powiązany z frazą {keyword}. W treści powinien znaleźć się jeden link HTML w postaci „<a href=\"{url}\">{keyword}</a>” do podstrony {url}, anchorem tego linku powinna być fraza kluczowa (może być odmieniona, może być zmieniona kolejność wyrazów, może zostać użyty synonim). Tekst umieść w <p></p>."
        
        response = await self.ask_openai(system, user, 180.0)

        text = self.remove_non_p_tags(response.choices[0].message.content)

        chance = randint(0,100)
        nf = ""
        if int(nofollow) > chance:
            nf = " rel=\"nofollow\""
            start = text.find("<a ")
            end = start + text[start:].find(">")
            text = text[:end] + nf + text[end:]

        if text.find(f"<a href=\"{url}\">{keyword}</a>") > 0:
            return header, text, int(response.usage.total_tokens), float(int(response.usage.total_tokens)*self.models_cost[self.text_model][1])
        elif text.find(f"<a href=\"{url}\"") > 0:
            #swap the keword
            base = text.find(f"<a href=\"{url}\"")
            start = base + text[base:].find(">")
            end = start + text[start:].find("</a")
            # print("Wrong keyword in ahref - ", text[base:end+4])
            # print(keyword)
            return header, text[:start+1]+keyword+text[end:], int(response.usage.total_tokens), float(int(response.usage.total_tokens)*self.models_cost[self.text_model][1])
        elif text.find("<a ") > 0:
            #swap link&keyword
            start = text.find("<a ")
            end = start + text[start:].find("</a")
            # print("Wrong link in anhor", text[start:end+4], start, end)
            # print(url, keyword)
            return header, text[:start+2] + " href=\""+url+"\""+nf+">"+keyword + text[end:], int(response.usage.total_tokens), float(int(response.usage.total_tokens)*self.models_cost[self.text_model][1])
        else:
            #generate again
            return await self.write_paragraph_linked(title, header, keyword, url, nofollow)


    async def write_description(self, text:str) -> tuple[str, int, float]:
        system =  "Jesteś wnikliwym autorem artykułów, który dokładnie opisuje wszystkie zagadnienia związane z tematem. Napisz tylko jeden paragraf"
        reduced_text = " ".join(text.split()[:500]) if len(text.split()) > 500 else text
        user = f'Dla poniższego artykułu napisz 4 zdania = jeden paragraf, podsumowujących jego treść i zachęcający czytelnika do przeczytania całości artykułu:\n{reduced_text}'
        
        response = await self.ask_openai(system, user, 260.0)

        return response.choices[0].message.content, int(response.usage.total_tokens), float(int(response.usage.total_tokens)*self.models_cost[self.text_model][1])
    

    async def create_img(self, img_prompt) -> str:
        client = OpenAI(api_key=self.api_key)
        helper = "Na zdjęciu znajdują się tylko nieruchome przedmioty. "
        try:
            response = client.images.generate(
                model=self.image_model,
                prompt=helper+img_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
        except openai.BadRequestError:
            new_prompt = await self.ask_openai(
                "You are moderator on an internet forum for kids. Rewrite given text, so it can be posted there.", 
                img_prompt,
                20.0
            )
            response = client.images.generate(
                model=self.image_model,
                prompt=helper+new_prompt.choices[0].message.content,
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
