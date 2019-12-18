
# import dependencies
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from html2text import html2text as htt
import pymysql, json, datetime, re

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
best_bets_table_id = 'sc-bTiqRo.LaLZW'
bestbets_insert = "INSERT INTO bestbets (rotation, league, date, match_details, play, line, odds, play_amount) values ({}, '{}', '{}', '{}', '{}', {}, {}, {});"
time_key = '(\d+)\:(\d+)([ap])'

# variables
driver = None
database = None
cursor = None

#BESTBETS rotation, league, date, match_details, play, line, odds, play_amount
#GAME league, home_team, away_team, date, home_win, away_win, home_proj_score, away_proj_score, home_spread, away_spread, home_total, away_total
#ODDS sport home_team, away_team, date, gome_c

# helper
def wait_for_element(class_name, by=By.CLASS_NAME):
	WebDriverWait(driver, element_timeout).until(EC.presence_of_element_located((by, class_name)))

def query (qu, *args):
	cursor.execute(qu.format(*args))
	database.commit()

def numstr(value):
	if value < 10: return '0' + str(value)
	else: return str(value)

# main
if __name__ == '__main__':

	# log into database
	#database = pymysql.connect(**json.load(open('database.json')))
	#database.close()

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
	today = datetime.date.today()
	wait_for_element('table', By.TAG_NAME)
	'''
	table = driver.find_element_by_tag_name('table')
	cells = table.text.split('\n')
	row = []
	for cell in cells[best_bets_column_count:]:
		row.append(cell)
		if len(row) > best_bets_column_count:

			# fix date and time
			datestr = row.pop(2)
			month, day = (int(item) for item in datestr.split('/'))
			if month < today.month: year = today.year + 1
			else: year = today.year
			hour, minute, apm = re.findall(time_key, row[2])[0]
			hour = int(hour)
			if apm == 'p': hour += 12
			minute = int(minute)
			row[2] = '{}-{}-{} {}:{}:00'.format(
				year, numstr(month), numstr(day),
				numstr(hour), numstr(minute),
			)

			# clean up
			row[7] = row[7][1:]

			# store
			print(bestbets_insert.format(*row))

			# reset
			row = []
	'''
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

