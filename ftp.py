from ftplib import FTP
import requests
from time import sleep

class UploadFTP:
    def __init__(self, \
                host:str, \
                name:str, \
                password:str, \
                path:str \
                ) -> None:
        

        self.wp_file = 'wp.zip'        
        self.do_ftp(host, name, password, path)


    def read(self, path):
        with open(path, "r") as f:
            return f.read().split('\n')
        

    def dir_del_r(self, server, dir):
        for i in server.nlst(dir):
            if(not i.endswith('.')):
                print("deleted", i)
                try:
                    server.delete(i)
                except Exception:
                    self.dir_del_r(server, i)
                    server.rmd(i)


    def do_ftp(self, h, u, p, path):
        with FTP(h, u, p) as server:
            print("Logged into FTP")
            server.cwd('public_html')
            #remove files from FTP (recursively)
            if not 'wp-admin' in server.nlst():
                self.dir_del_r(server, '')

                #upload files to FTP
                with open(path + '/' + self.wp_file, 'rb') as file:
                    server.storbinary('STOR ' + self.wp_file, file)                

                with open(path + '/wypakuj.php', 'rb') as file:
                    server.storbinary('STOR wypakuj.php', file)

                #ping to unpack .zip
                print("Unpacking WordPress")
                self.ping_unpack(h)
            else:
                print("Wordpress already on FTP")

            
            #clean trash afterwards
            if self.wp_file in server.nlst(): server.delete(self.wp_file)
            if 'wypakuj.php' in server.nlst(): server.delete('wypakuj.php')


    def ping_unpack(self, url):
        code = 0
        while code != 200:
            code = requests.get("http://" + url + "/wypakuj.php", verify=False).status_code
            print(code)
            if code == 200: break
            sleep(2)


if __name__ == "__main__":
    pass