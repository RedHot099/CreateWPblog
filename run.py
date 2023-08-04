import json
from time import time

from create import Create
from ftp import UploadFTP
from setup_wp import Setup_WP
from openai_article import OpenAI_article


with open("credentials.json", "r") as creds:
		credentials = json.load(creds)
            

with open("input.txt", "r") as f:
    domains = [x.split(' ') for x in f.read().split('\n')]



for domain, topic, lang in domains:
    start_time = time()
    print("{s:{x}^{n}}".format(s=domain, x='=', n=30))
    create = Create(credentials["vd"])
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
    
    wp_api_key = wp.get_api_key(uname, pwd)


    o = OpenAI_article(
            api_key=credentials["api"],
            domain_name=domain,
            wp_login=uname,
            wp_pass=wp_api_key,
            lang=lang
    )

    o.create_structure(topic, 4, 2)

    o.populate_structure(article_num=2, header_num=6, days_delta=7, forward_delta=False)

    o.populate_structure(article_num=8, header_num=2, days_delta=3, forward_delta=False)

    print(f"{f'{time()-start_time}s':=^30}")
