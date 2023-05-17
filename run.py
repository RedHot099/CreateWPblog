import json

from create import Create
from ftp import UploadFTP
from setup_wp import Setup_WP
from openai_article import OpenAI_article


with open("credentials.json", "r") as creds:
		credentials = json.load(creds)
                

create = Create(credentials["vd20"])

domain_topics = create.do_stuff("input.txt")

data = []

with open("results.tsv", "r") as results:
    data = [r.split("\t") for r in results.read().split("\n")]


for row, topic in zip(data,domain_topics):
    if row == ['']:
        pass
    print(f"======={row[0]}=======")
    print("Connecting to FTP")
    f = UploadFTP(row[0], row[3], row[4], "C:/Users/Kuba/Documents/praca/Zaplecza/pliki-artur")
    print("Initilazing WP setup")
    wp = Setup_WP(row[0])

    uname, pwd = wp.install(row[1], row[2], row[0].partition(".")[0])
    with open("credentials.tsv", "a+") as output:
        output.write(f"{row[0]}\t{uname}\t{pwd}\n")
    print("Tweaking WP options")
    wp.setup(uname, pwd)
    """
    print("Getting API key")
    wp = Setup_WP(row[0])
    api_key = wp.get_api_key(uname, pwd)

    openai = OpenAI_article(
          api_key=api_key, 
          domain_name=row[0],
          wp_login=uname,
          wp_pass=pwd
    )

    if topic == '':
        input(f"O jakiej tematyce pisać artykuły na strone {row[0]}")

    openai.create_structure(
          topic=topic,
          category_num=3,
          subcategory_num=3, 
          article_num=3, 
          header_num=4, 
          days_delta=7,
          forward_delta=False
    )
    """
    