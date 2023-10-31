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
import os


class Create:
	def __init__(self, \
				credentials: dict \
				) -> None:
		#login credentials
		self.user = credentials["login"]
		self.password = credentials["password"]
		if credentials["url"].startswith("http"):
			self.panel = credentials["url"]
		else:
			self.panel = "http://"+credentials["url"]
		if self.panel.endswith("/"):
			self.panel = self.panel[:-1]

		options = webdriver.ChromeOptions()
		options.add_experimental_option('excludeSwitches', ['enable-logging'])
		options.add_argument('--no-sandbox')
		options.add_argument('--window-size=1420,1080')
		options.add_argument('--headless')
		options.add_argument('--disable-gpu')
		options.add_argument('ignore-certificate-errors')
		if os.path.isfile('/usr/lib/chromium-browser/chromedriver'):
			self.driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=options)
		else:
			self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
		
	
	def read(self, path):
		with open(path, "r") as f:
			return f.read().split('\n')
		
	def login(self):
		print("Logging into panel")
		self.driver.get(f"{self.panel}/")
		# sleep(1)
		WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#username"))).send_keys(self.user)
		WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#password"))).send_keys(self.password)
		self.driver.execute_script("document.getElementsByTagName('button')[0].click()")
		sleep(1)
		return self.driver
				
	def add_domain(self, name: str):
		print("Creating domain base")
		self.driver.execute_script(f"window.open('{self.panel}/user/domains/add-domain');")
		sleep(0.2)
		self.driver.switch_to.window(self.driver.window_handles[1])
		WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.input-text.grow")))
		self.driver.find_elements(By.CSS_SELECTOR, "input.input-text.grow")[0].send_keys(name)
		sleep(2)
		WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.-theme-primary.-size-big")))
		self.driver.find_element(By.CSS_SELECTOR, "button.-theme-primary.-size-big").click()
		sleep(0.2)
		
		
	def add_ip(self, name:str):
		print("IP", name)
		#Adding domain
		sleep(1)
		try:
			self.driver.get(f'{self.panel}/user/domains/domain/{name}/ips')
			WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.q-virtual-scroll__content")))
		except:
			print("Cannot set IP")
			return -1
		ip = s.gethostbyname(name)
		if (self.driver.find_element(By.CSS_SELECTOR, "tbody.q-virtual-scroll__content > tr > td:nth-child(2)").get_attribute("innerText") != ip):
			self.driver.find_elements(By.CSS_SELECTOR, "a.ui-useful-links-entry")[0].click()
			if (self.driver.find_element(By.CSS_SELECTOR, "span.Select__Button__Label").get_attribute("innerText") != ip):
				self.driver.find_element(By.CSS_SELECTOR, "div.Select>button.Select__Button").click()
				for i in self.driver.find_elements(By.CSS_SELECTOR, "span.Select__Dropdown__Items__Item"):
					print("Dostępny ip - "+i.get_attribute("innerText"), i.get_attribute("innerText")==ip)
					if i.get_attribute("innerText") == ip:
						i.click()
						break
			try:
				self.driver.find_element(By.CSS_SELECTOR, "button.-theme-primary.-size-big").click()
			except:
				print("Brak adresu IP w puli - " + ip)


	def add_ssl(self):
		print("SSL")
		#SSL
		self.driver.get(f'{self.panel}/user/ssl/server/')
		# sleep(1)
		WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.input-checkbox-control")))
		self.driver.find_elements(By.CSS_SELECTOR, "div.input-checkbox-control")[0].click()
		self.driver.find_element(By.CSS_SELECTOR, "button.-theme-safe").click()	
		sleep(0.2)


	def add_db(self, name:str):
		print("DataBase")
		#DB
		self.driver.get(f'{self.panel}/user/database/create')
		WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.input-text"))).send_keys(name.partition('.')[0])
		WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.inputPassword>div>div>div>button"))).click()
		sleep(0.5)
		WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.-theme-safe.-size-big"))).click()

		#Copy db creds
		sleep(2)
		db_creds = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "dialog-content-wrapper"))).get_attribute("innerText").split('\n')
		db_creds = list(filter(None, db_creds))
		db_user = db_creds[-2].split('\t')[-1]
		db_pass = db_creds[-1].split('\t')[-1]

		print(f"{db_user} : {db_pass}")
		return db_user, db_pass
	
	
	def add_ftp(self):
		print("FTP")
		#FTP
		self.driver.get(f'{self.panel}/user/ftp-accounts/create')
		#change domain
		if(not self.panel.endswith(WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span.domain"))).get_attribute("innerText"))):
			print("Wrong domain: "+ self.driver.find_element(By.CSS_SELECTOR, "span.domain").get_attribute("innerText"))
			self.driver.find_element(By.CSS_SELECTOR, "span.domain").click()
			for a in self.driver.find_elements(By.CSS_SELECTOR, "a#refreshed-domain-select-dropdown-item"):
				if self.panel.endswith(a.get_attribute("innerText")):
					a.click()
					break
		# sleep(1)
		WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.input-text"))).send_keys("admin")
		WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.inputPassword>div>div>div>button"))).click()
		sleep(1.5)
		WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.button.-theme-safe.-size-big"))).click()

		#Copy ftp creds
		sleep(1)
		print(self.driver.current_url)
		ftp_creds = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "dialog-content-wrapper"))).get_attribute("innerText").split('\n')
		ftp_creds = list(filter(None, ftp_creds))
		ftp_user = ftp_creds[0].split('\t')[1]
		ftp_pass = ftp_creds[1].split('\t')[1]

		print(f"{ftp_user} : {ftp_pass}")

		return ftp_user, ftp_pass
	

	def do_stuff(self, name:str) -> list[str]:
		self.login()

		self.add_domain(name)
		self.add_ip(name)
		self.add_ssl()
		
		db_user, db_pass = self.add_db(name)
		ftp_user, ftp_pass = self.add_ftp()

		#close tab and switch to main
		try:
			self.driver.close()
			self.driver.switch_to.window(self.driver.window_handles[0])
		except:
			print("Cannot close tab")

		self.driver.close()
		return db_user, db_pass, ftp_user, ftp_pass



if __name__ == "__main__":
	pass