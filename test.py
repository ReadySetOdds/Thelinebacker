from selenium import webdriver
import requests
import time
from bs4 import BeautifulSoup


driver = webdriver.PhantomJS()
driver.set_window_size(1120, 550)
driver.get("https://www.predictionmachine.com/signin")
for element in driver.find_elements_by_tag_name('input'):
    name = element.get_attribute('name')
    if name == 'email':
        element.send_keys('rmarshallsmith@hotmail.com')
    elif name == 'password':
        element.send_keys('football2020')
for element in driver.find_elements_by_tag_name('button'):
    print(element.get_attribute('data-cy'))
    if element.get_attribute('data-cy') == 'signin-submit':
        element.click()
        print("yay!")
        break

time.sleep(5)
print(driver.current_url)
