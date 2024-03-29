from time import sleep
import socket as s
from datetime import date, datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
import os


class Setup_WP:
	def __init__(self, 
                url: str = "", 
				email: str = "jeichner@verseo.pl",
				lang: str = "pl",
				ssl: bool = False
				) -> None:
		
		#login credentials
		if ssl:
			self.url = "https://"+url
		else:
			self.url = "http://"+url

		self.lang = lang
		self.email = email

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
		

	def start(self):
		self.get_url(f"{self.url}/")
		WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "button")))

		#select language
		if WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#language-continue"))):
			self.driver.find_element(By.CSS_SELECTOR, f"option[lang=\"{self.lang}\"]").click()
			sleep(1)
			self.driver.find_element(By.CLASS_NAME, "button").click()

		WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "button"))).click()
		sleep(1)

	
	def get_url(self, url:str):
		try:
			self.driver.get(url)
		except Exception as e:
			print(e)
		if self.driver.current_url.split('/')[-1].startswith("upgrade"):
			self.driver.find_element(By.CLASS_NAME, "button").click()
			sleep(1.5)
			self.driver.get(url)
			sleep(0.5)
		print(self.driver.current_url)



	def connect_db(self, db_name:str, db_pass:str):
		try:
			WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.ID, "dbname")))
		except:
			if self.driver.find_element(By.ID, "weblog_title"): return -1
			
		self.driver.find_element(By.ID, "dbname").clear()
		self.driver.find_element(By.ID, "dbname").send_keys(db_name)
		self.driver.find_element(By.ID, "uname").clear()
		self.driver.find_element(By.ID, "uname").send_keys(db_name)
		self.driver.find_element(By.ID, "pwd").clear()
		self.driver.find_element(By.ID, "pwd").send_keys(db_pass)
		self.driver.find_element(By.CLASS_NAME, "button").click()
		sleep(1)
		self.driver.find_element(By.CLASS_NAME, "button").click()
		sleep(1)


	def give_name(self, name: str) -> tuple[str, str]:
		WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "weblog_title")))
		self.driver.find_element(By.ID, "weblog_title").clear()
		self.driver.find_element(By.ID, "weblog_title").send_keys(name)
		self.driver.find_element(By.ID, "user_login").send_keys("admin")
		uname = self.driver.find_element(By.ID, "user_login").get_attribute("value")
		pwd = self.driver.find_element(By.ID, "pass1").get_attribute('value')

		WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, "admin_email")))
		self.driver.find_element(By.ID, "admin_email").send_keys(self.email)
		self.driver.find_element(By.ID, "submit").click()
		sleep(1)
		self.driver.find_element(By.CLASS_NAME, "button").click()
		sleep(1)
		return uname, pwd
	
		
	def login(self, login:str, pwd: str):
		self.get_url(f"{self.url}/wp-login.php")
		WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, "user_login")))
		self.driver.find_element(By.ID, "user_login").clear()
		self.driver.find_element(By.ID, "user_login").send_keys(login)
		self.driver.find_element(By.ID, "user_pass").clear()
		self.driver.find_element(By.ID, "user_pass").send_keys(pwd)
		try:
			self.driver.find_element(By.ID, "wp-submit").click()
		except:
			print("User already logged in")
		sleep(1)
		try:
			self.driver.find_element(By.ID, "login_error")
			return 0
		except:
			WebDriverWait(self.driver, 15).until(
				lambda driver: EC.presence_of_element_located((By.ID, "wpwrap")) or EC.presence_of_element_located((By.CSS_SELECTOR, "h1.admin-email__heading"))
				)
			return 1


	def delete_posts(self):
		self.get_url(f"{self.url}/wp-admin/edit.php")
		try:
			WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.ID, "cb-select-all-1")))
			self.driver.find_element(By.ID, "cb-select-all-1").click()
		except:
			sleep(2)
			self.get_url(f"{self.url}/wp-admin/edit.php")
			WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.ID, "cb-select-all-1")))
			self.driver.find_element(By.ID, "cb-select-all-1").click()
		try:
			WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.ID, "bulk-action-selector-top")))
			self.driver.find_element(By.ID, "bulk-action-selector-top").click()
			self.driver.find_element(By.ID, "bulk-action-selector-top").find_element(By.XPATH, "//option[@value='trash']").click()
			self.driver.find_element(By.ID, "doaction").click()
			sleep(1)
			return 0
		except:
			return -1



	def delete_pages(self):
		self.get_url(f"{self.url}/wp-admin/edit.php?post_type=page")
		try:
			WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.ID, "cb-select-all-1")))
			self.driver.find_element(By.ID, "cb-select-all-1").click()
		except:
			sleep(1)
			self.get_url(f"{self.url}/wp-admin/edit.php?post_type=page")
			WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.ID, "cb-select-all-1")))
			self.driver.find_element(By.ID, "cb-select-all-1").click()
		WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.ID, "bulk-action-selector-top")))
		self.driver.find_element(By.ID, "bulk-action-selector-top").click()
		self.driver.find_element(By.ID, "bulk-action-selector-top").find_element(By.XPATH, "//option[@value='trash']").click()
		self.driver.find_element(By.ID, "doaction").click()
		sleep(1)


	def activate_plugins(self):
		self.get_url(f"{self.url}/wp-admin/plugins.php")
		try:
			WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.ID, "cb-select-all-1")))
			self.driver.find_element(By.ID, "cb-select-all-1").click()
		except:
			sleep(1)
			self.get_url(f"{self.url}/wp-admin/plugins.php")
			WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.ID, "cb-select-all-1")))
			self.driver.find_element(By.ID, "cb-select-all-1").click()
		WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.ID, "bulk-action-selector-top")))
		self.driver.find_element(By.ID, "bulk-action-selector-top").click()
		self.driver.find_element(By.ID, "bulk-action-selector-top").find_element(By.XPATH, "//option[@value='activate-selected']").click()
		self.driver.find_element(By.ID, "doaction").click()
		sleep(15)



	def checkbox_checked(self, id:str, check:bool):
		if id == "":
			return False
		checkbox = self.driver.find_element(By.ID, id)
		if check != (True if checkbox.get_attribute('checked') == "true" else False):
			checkbox.click()


	def setup_menu(self):
		self.get_url(f"{self.url}/wp-admin/nav-menus.php?action=edit&menu=0")
		try:
			WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, "menu-name"))).send_keys("main")
		except:
			sleep(3)
			self.get_url(f"{self.url}/wp-admin/nav-menus.php?action=edit&menu=0")
			WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, "menu-name"))).send_keys("main")
		self.driver.find_element(By.ID, "locations-primary").click()
		self.driver.find_element(By.ID, "locations-secondary").click()
		self.driver.find_element(By.ID, "save_menu_footer").click()
		self.driver.find_element(By.ID, "show-settings-link").click()
		WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.ID, "add-shortcode-section-hide"))).click()
		sleep(2)
		self.driver.find_element(By.ID, "add-shortcode-section").click()
		self.driver.find_element(By.ID, "aau-ahcm-shortcode").send_keys("[autocategorymenu hide_empty=\"1\"]")
		WebDriverWait(self.driver, 33).until(EC.element_to_be_clickable((By.ID, "submit-aau-ahcm"))).click()
		sleep(2)
		self.driver.find_element(By.ID, "save_menu_footer").click()
		sleep(2.5)

	
	def settings(self):
		#general settings
		self.get_url(f"{self.url}/wp-admin/options-general.php")
		WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, "blogdescription")))
		self.driver.find_element(By.ID, "blogdescription").clear()
		self.driver.find_element(By.ID, "submit").click()
		sleep(0.5)
		#discussion settings
		self.get_url(f"{self.url}/wp-admin/options-discussion.php")
		WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "fieldset")))
		for i, fieldset in enumerate(self.driver.find_elements(By.TAG_NAME, "fieldset")):
			if i%2:
				for box in fieldset.find_elements(By.TAG_NAME, "input"):
					self.checkbox_checked(box.get_attribute('id'), True)
			else:
				for box in fieldset.find_elements(By.TAG_NAME, "input"):
					self.checkbox_checked(box.get_attribute('id'), False)
		self.driver.find_element(By.ID, "submit").click()
		sleep(1)
		#permalink settings
		self.get_url(f"{self.url}/wp-admin/options-permalink.php")
		WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, "permalink-input-post-name")))
		self.driver.find_element(By.ID, "permalink-input-post-name").click()
		self.driver.find_element(By.ID, "submit").click()
		sleep(1)

	def get_api_key(self, login:str, pwd:str) -> str:
		logged = self.login(login, pwd)
		if(not logged):
			return "Wrong password"
		self.get_url(f"{self.url}/wp-admin/profile.php")
		WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "new_application_password_name")))
		self.driver.find_element(By.ID, "new_application_password_name").send_keys("api-"+datetime.now().strftime('%d-%m-%Y-%f'))
		try:
			WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.ID, "do_new_application_password"))).click()
		except:
			print(self.driver.page_source)
		sleep(3)
		try:
			print("API key: ", self.driver.find_element(By.ID, "new-application-password-value").get_attribute("value"))
		except:
			print("No key value")
		try:
			api_key = WebDriverWait(self.driver, 6).until(EC.presence_of_element_located((By.ID, "new-application-password-value"))).get_attribute("value")
		except:
			raise LookupError
		self.driver.close()
		return str(api_key)


	def install(self, db_name:str, db_pass:str, name:str) -> tuple[str,str]:
		self.start()
		self.connect_db(db_name, db_pass)
		uname, pwd = self.give_name(name)
		return uname, pwd

	
	def setup(self, login:str, pwd:str):
		self.login(login, pwd)
		test = self.delete_posts()
		if test == -1: return -1
		self.delete_pages()
		self.activate_plugins()
		self.setup_menu()
		self.settings()
		sleep(1)
		self.driver.close()
	

if __name__ == "__main__":
	pass