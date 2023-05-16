from time import sleep
import socket as s

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


class Setup_WP:
	def __init__(self, 
                url: str = ""
				) -> None:
		
		#login credentials
		self.url = url
		
		options = webdriver.ChromeOptions()
		options.add_experimental_option('excludeSwitches', ['enable-logging'])
		options.add_argument('--headless=new')
		options.add_argument('ignore-certificate-errors')
		self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
		
	
	def read(self, path):
		with open(path, "r") as f:
			return f.read().split('\n')
		

	def start(self):
		self.driver.get(f"http://{self.url}/")
		sleep(1)
		self.driver.find_element(By.CLASS_NAME, "button").click()
		sleep(1)


	def connect_db(self, db_name:str, db_pass:str):
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


	def give_name(self, name: str) -> str:
		self.driver.find_element(By.ID, "weblog_title").clear()
		self.driver.find_element(By.ID, "weblog_title").send_keys(name)
		self.driver.find_element(By.ID, "user_login").send_keys("admin")
		uname = self.driver.find_element(By.ID, "user_login").get_attribute("value")
		pwd = self.driver.find_element(By.ID, "pass1").get_attribute('value')
		self.driver.find_element(By.ID, "admin_email").send_keys("jeichner@verseo.pl")
		self.driver.find_element(By.ID, "submit").click()
		sleep(1)
		self.driver.find_element(By.CLASS_NAME, "button").click()
		sleep(1)
		return uname, pwd
	
		
	def login(self, login:str, pwd: str):
		self.driver.get(f"https://{self.url}/wp-admin")
		sleep(1)
		self.driver.find_element(By.ID, "user_login").clear()
		self.driver.find_element(By.ID, "user_login").send_keys(login)
		self.driver.find_element(By.ID, "user_pass").clear()
		self.driver.find_element(By.ID, "user_pass").send_keys(pwd)
		self.driver.find_element(By.ID, "wp-submit").click()
		sleep(1)


	def delete_posts(self):
		self.driver.get(f"https://{self.url}/wp-admin/edit.php")
		sleep(1)
		try:
			self.driver.find_element(By.ID, "cb-select-all-1").click()
		except NoSuchElementException:
			sleep(2)
			self.driver.get(f"https://{self.url}/wp-admin/edit.php")
			sleep(1)
			self.driver.find_element(By.ID, "cb-select-all-1").click()
		self.driver.find_element(By.ID, "bulk-action-selector-top").click()
		self.driver.find_element(By.ID, "bulk-action-selector-top").find_element(By.XPATH, "//option[@value='trash']").click()
		self.driver.find_element(By.ID, "doaction").click()
		sleep(1)



	def delete_pages(self):
		self.driver.get(f"https://{self.url}/wp-admin/edit.php?post_type=page")
		sleep(1)
		self.driver.find_element(By.ID, "cb-select-all-1").click()
		self.driver.find_element(By.ID, "bulk-action-selector-top").click()
		self.driver.find_element(By.ID, "bulk-action-selector-top").find_element(By.XPATH, "//option[@value='trash']").click()
		self.driver.find_element(By.ID, "doaction").click()
		sleep(1)


	def checkbox_checked(self, id:str, check:bool):
		if id == "":
			return False
		checkbox = self.driver.find_element(By.ID, id)
		if checkbox.get_attribute('checked'):
			if not check:
				checkbox.click()
		else:
			if check:
				checkbox.click()

	
	def settings(self):
		#general settings
		self.driver.get(f"https://{self.url}/wp-admin/options-general.php")
		self.driver.find_element(By.ID, "blogdescription").clear()
		self.driver.find_element(By.ID, "submit").click()
		sleep(0.5)
		#discussion settings
		self.driver.get(f"https://{self.url}/wp-admin/options-discussion.php")
		sleep(0.5)
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
		self.driver.get(f"https://{self.url}/wp-admin/options-permalink.php")
		sleep(0.1)
		self.driver.find_element(By.ID, "permalink-input-post-name").click()
		self.driver.find_element(By.ID, "submit").click()
		sleep(1)

	def get_api_key(self):
		self.driver.get(f"https://{self.url}/wp-admin/profile.php")
		self.driver.find_element(By.ID, "new_application_password_name").send_keys("api")
		self.driver.find_element(By.ID, "do_new_application_password").click()
		api_key = self.driver.find_element(By.ID, "new-application-password-value").get_attribute("innerText")
		print("API KEY: ", api_key)
		return api_key


	def install(self, db_name:str, db_pass:str, name:str):
		self.start()
		self.connect_db(db_name, db_pass)
		pwd = self.give_name(name)
		return pwd

	
	def setup(self, login:str, pwd:str):
		self.login(login, pwd)
		self.delete_posts()
		self.delete_pages()
		self.settings()
		sleep(1)
		self.driver.close()
		return self.get_api_key()




		



if __name__ == "__main__":
	z = Setup_WP("sibi-ev.de")
	z.setup("admin", "qStuuK@PU6h8X$wC9!")