from ftplib import FTP
import requests

class UploadFTP:
    def __init__(self, \
                host:str, \
                name:str, \
                password:str, \
                path:str \
                ) -> None:
        
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
            server.cwd('public_html')
            #remove files from FTP (recursively)
            if not 'dodaj_tagi_artur_v1.php' in server.nlst():
                self.dir_del_r(server, '')

                #upload files to FTP
                file = open(path + '/wordpress-artur.zip', 'rb')
                server.storbinary('STOR wordpress-artur.zip', file)
                file.close()
                file = open(path + '/wypakuj.php', 'rb')
                server.storbinary('STOR wypakuj.php', file)
                file.close()

                #ping to unpack .zip
                self.ping_unpack(h)
            else:
                print("Wordpress already on FTP")

            
            #clean trash afterwards
            if 'wordpress-artur.zip' in server.nlst(): server.delete('wordpress-artur.zip')
            if 'wypakuj.php' in server.nlst(): server.delete('wypakuj.php')


    def ping_unpack(self, url):
        requests.get("http://" + url + "/wypakuj.php", verify=False)


if __name__ == "__main__":
    pass