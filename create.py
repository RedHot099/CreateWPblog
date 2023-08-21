from time import sleep
import socket as s
import json

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class Create:
	def __init__(self, \
				credentials: dict \
				) -> None:
		
		#login credentials
		self.user = credentials["login"]
		self.password = credentials["password"]
		self.panel = credentials["url"]

		options = webdriver.ChromeOptions()
		options.add_argument('--no-sandbox')
		options.add_argument('--disable-dev-shm-usage')
		options.add_experimental_option('excludeSwitches', ['enable-logging'])
		options.add_argument('--headless=new')
		options.add_argument('ignore-certificate-errors')
		self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
		
	
	def read(self, path):
		with open(path, "r") as f:
			return f.read().split('\n')
		
	def login(self):
		print("Logging into panel")
		self.driver.get(f"http://{self.panel}/")
		# sleep(1)
		WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "input")))
		self.driver.find_element("id", "username").find_element(By.TAG_NAME, "input").send_keys(self.user)
		self.driver.find_element("id", "password").find_element(By.TAG_NAME, "input").send_keys(self.password)
		self.driver.execute_script("document.getElementsByTagName('button')[0].click()")
		sleep(1)
		return self.driver
				
	def add_domain(self, name: str):
		print("Creating domain base")
		self.driver.execute_script(f"window.open('http://{self.panel}/user/domains/add-domain');")
		sleep(1)
		self.driver.switch_to.window(self.driver.window_handles[1])
		# sleep(2)
		WebDriverWait(self.driver, 33).until(EC.element_to_be_clickable((By.TAG_NAME, "input")))
		self.driver.find_elements(By.TAG_NAME, "input")[1].send_keys(name)
		sleep(1)
		self.driver.find_elements(By.TAG_NAME, "button")[2].click()
		
		
	def add_ip(self, name:str):
		print("IP", name)
		#Adding domain
		sleep(1)
		self.driver.get(f'http://{self.panel}/user/domains/domain/{name}/ips')
		WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > div.app.fx\:cross\:stretch.width\:100\% > div.standard-2021-layout > main > section > div > div.standard-page-wrapper > div.standard-page-content > section > div.r-table > div.ui-table.scrollbar\:primary > table > tbody.q-virtual-scroll__content > tr > td:nth-child(2)")))
		# sleep(1)
		ip = s.gethostbyname(name)
		if (self.driver.find_element(By.CSS_SELECTOR, "body > div.app.fx\:cross\:stretch.width\:100\% > div.standard-2021-layout > main > section > div > div.standard-page-wrapper > div.standard-page-content > section > div.r-table > div.ui-table.scrollbar\:primary > table > tbody.q-virtual-scroll__content > tr > td:nth-child(2)").get_attribute("innerText") != ip):
			self.driver.find_elements(By.CSS_SELECTOR, "a.ui-useful-links-entry")[0].click()
			if (self.driver.find_element(By.CSS_SELECTOR, "span.Select__Button__Label").get_attribute("innerText") != ip):
				self.driver.find_element(By.CSS_SELECTOR, "div.Select>button.Select__Button").click()
				for i in self.driver.find_elements(By.CSS_SELECTOR, "span.Select__Dropdown__Items__Item"):
					if i.get_attribute("innerText") == ip:
						i.click()
						break
			try:
				self.driver.find_element(By.CSS_SELECTOR, "div.dialog-buttons > button.-theme-primary").click()
			except:
				print("Brak adresu IP w puli - " + ip)


	def add_ssl(self):
		print("SSL")
		#SSL
		self.driver.get(f'http://{self.panel}/user/ssl/server/')
		# sleep(1)
		WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.input-checkbox-control")))
		self.driver.find_elements(By.CSS_SELECTOR, "div.input-checkbox-control")[0].click()
		self.driver.find_element(By.CSS_SELECTOR, "body > div.app.fx\:cross\:stretch.width\:100\% > div.standard-2021-layout > main > section > div > div.standard-page-wrapper > div.standard-page-content > div:nth-child(1) > div > div > div.formElement-content.fxi\:grow\:true.fxi\:shrink\:true.fx\:dir\:row.fx\:cross\:center.fx\:equalWidth\:true > div > div > button").click()	
		sleep(0.2)


	def add_db(self, name:str):
		print("DataBase")
		#DB
		self.driver.get(f'http://{self.panel}/user/database/create')
		# sleep(1)
		WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "input")))
		self.driver.find_elements(By.TAG_NAME, "input")[1].send_keys(name.partition('.')[0])
		self.driver.find_element(By.CSS_SELECTOR, "div.inputPassword>div>div>div>button").click()
		sleep(0.5)
		self.driver.find_element(By.CSS_SELECTOR, "div.footer-buttons-slot>button").click()

		#Copy db creds
		sleep(1)
		db_creds = self.driver.find_element(By.CLASS_NAME, "dialog-content-wrapper").get_attribute("innerText").split('\n')
		db_user = db_creds[3].split('\t')[1]
		db_pass = db_creds[4].split('\t')[1]

		print(f"{db_user} : {db_pass}")
		return db_user, db_pass
	
	
	def add_ftp(self):
		print("FTP")
		#FTP
		self.driver.get(f'http://{self.panel}/user/ftp-accounts/create')
		# sleep(1)
		WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "input")))
		self.driver.find_elements(By.TAG_NAME, "input")[1].send_keys("admin")
		self.driver.find_element(By.CSS_SELECTOR, "div.inputPassword>div>div>div>button").click()
		sleep(0.5)
		self.driver.find_element(By.CSS_SELECTOR, "div.footer-buttons-slot>button").click()

		#Copy ftp creds
		sleep(1)
		ftp_creds = self.driver.find_element(By.CLASS_NAME, "dialog-content-wrapper").get_attribute("innerText").split('\n')
		ftp_user = ftp_creds[0].split('\t')[1]
		ftp_pass = ftp_creds[1].split('\t')[1]

		print(f"{ftp_user} : {ftp_pass}")

		return ftp_user, ftp_pass
	

	def do_stuff(self, name:str) -> list[str]:
		self.login()

		with open("results.tsv", "a+") as output:
			self.add_domain(name)
			self.add_ip(name)
			self.add_ssl()
			
			db_user, db_pass = self.add_db(name)
			ftp_user, ftp_pass = self.add_ftp()				
			
			output.write(f'{name}\t{db_user}\t{db_pass}\t{ftp_user}\t{ftp_pass}\n')
	
			#close tab and switch to main
			self.driver.close()
			self.driver.switch_to.window(self.driver.window_handles[0])

			self.driver.close()
			return db_user, db_pass, ftp_user, ftp_pass



if __name__ == "__main__":
	pass