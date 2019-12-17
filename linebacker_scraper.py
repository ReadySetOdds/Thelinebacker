
# import dependencies
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from html2text import html2text as htt

# constants
linebacker_username = 'rmarshallsmith@hotmail.com'
linebacker_password = 'football2020'
signin_url = 'https://www.thelinebacker.com/signin'
initial_games_url = 'https://www.thelinebacker.com/{}/games'
games_url = initial_games_url + '/{}'
odds_url = 'https://www.thelinebacker.com/odds/{}'
best_bets_column_count = 8
element_timeout = 30
weeks_dropdown_class = 'sc-iFMziU.lkmqRa'
games_table_class = 'sc-RbTVP.beCBks'
odds_table_class = 'chalk-event'
table_indices = (0, 2, 10, 12, 16, 18, 26, 28, 36, 38, 44, 48, 50, 56, 60)

# variables
driver = None


# helper
def wait_for_element(class_name, by=By.CLASS_NAME):
	WebDriverWait(driver, element_timeout).until(EC.presence_of_element_located((by, class_name)))


# main
if __name__ == '__main__':
	
	# start driver
	driver = webdriver.Firefox()
	
	# log into page
	driver.get(signin_url)
	for element in driver.find_elements_by_tag_name('input'):
		name = element.get_attribute('name')
		if name == 'email':
			element.send_keys(linebacker_username)
		elif name == 'password':
			element.send_keys(linebacker_password)
	for element in driver.find_elements_by_tag_name('button'):
		if element.text == 'Log in':
			element.click()
			break
	
	# get best bets
	wait_for_element('table', by=By.TAG_NAME)
	while True:
		element_found = False
		for element in driver.find_elements_by_tag_name('table'):
			element_found = True
			table = element
			break
		if element_found: break
	cells = table.text.split('\n')
	row = []
	for cell in cells[best_bets_column_count:]:
		row.append(cell)
		if len(row) > best_bets_column_count: pass#DATAOP

	# go to sports
	for sport in ('NFL', 'NCAAF', 'NBA', 'NCAAB', 'MLB', 'NHL'):

		# initalize games page
		driver.get(initial_games_url.format(sport.lower()))
		wait_for_element(weeks_dropdown_class)

		# get games data
		last_url = ''
		week = 1
		while True:

			# go to page
			driver.get(games_url.format(sport.lower(), week))
			wait_for_element(games_table_class)
			if driver.current_url == last_url: break

			# go through tables
			for table in driver.find_elements_by_class_name(games_table_class):
				data = htt(table.get_attribute('innerHTML')).split('\n')
				for index in table_indices: pass#DATAOP

			# update
			week += 1
			last_url = driver.current_url

		# get odds data
		driver.get(odds_url.format(sport.lower()))
		wait_for_element(odds_table_class)
		for table in driver.find_elements_by_class_name(odds_table_class):
			data = htt(table.text).split()
			#DATAOP

