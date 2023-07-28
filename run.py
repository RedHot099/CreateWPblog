import json

from create import Create
from ftp import UploadFTP
from setup_wp import Setup_WP
from openai_article import OpenAI_article


with open("credentials.json", "r") as creds:
		credentials = json.load(creds)
            


with open("input.txt", "r") as f:
    domains = f.read().split('\n')



for domain in domains:
    print(f"======={domain}=======")
    create = Create(credentials["vd09"])
    db_user, db_pass, ftp_user, ftp_pass = create.do_stuff(domain)

    print("Connecting to FTP")
    f = UploadFTP(domain, ftp_user, ftp_pass, "files")

    print("Initilazing WP setup")
    wp = Setup_WP(domain)

    uname, pwd = wp.install(db_user, db_pass, domain.partition(".")[0])
    with open("credentials.tsv", "a+") as output:
        output.write(f"{domain}\t{uname}\t{pwd}\n")
    print("Tweaking WP options")
    wp.setup(uname, pwd)



    
"""
print("Getting API key")
wp = Setup_WP(domain)
api_key = wp.get_api_key(uname, pwd)

openai = OpenAI_article(
        api_key=api_key, 
        domain_name=domain,
        wp_login=uname,
        wp_pass=pwd
)

if topic == '':
    input(f"O jakiej tematyce pisać artykuły na strone {domain}")

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
