
# import dependencies
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from html2text import html2text as htt
import pymysql, json, datetime, re, os

# constants
linebacker_username = 'rmarshallsmith@hotmail.com'
linebacker_password = 'football2020'
signin_url = 'https://www.thelinebacker.com/signin'
initial_games_url = 'https://www.thelinebacker.com/{}/games'
games_url = initial_games_url + '/{}'
odds_url = 'https://www.thelinebacker.com/odds/{}'
best_bets_column_count = 8
element_timeout = 60
calendar_button = 'sc-feWbDf.bVBUqB.sc-htoDjs.iArBBn'
weeks_dropdown_button_class = 'sc-keVrkP.ktOnIp'
weeks_dropdown_list_class = 'sc-exkUMo.hyEDPn'
games_table_class = 'sc-jqIZGH.dYoubK'
odds_table_class = 'chalk-event'
table_indices = (0, 2, 10, 12, 16, 18, 26, 28, 36, 38, 44, 48, 50, 56, 60)
best_bets_table_id = 'sc-bTiqRo.LaLZW'
bestbets_insert = "INSERT INTO bestbets (rotation, league, date, match_details, play, line, odds, play_amount) values ({}, '{}', '{}', '{}', '{}', {}, {}, {});"
games_insert = "INSERT INTO games (league, home_team, away_team, date, home_win, away_win, home_proj_score, away_proj_score, spread_total, home_spread_1, home_spread_2, away_spread_1, away_spread_2, total, home_total, odds_under, away_total, odds_total) values ('{}', '{}', '{}', '{}', {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {});"
odds_insert = "INSERT INTO odds (league, home_team, away_team, date, odds_group, home_odds_1, home_odds_2, away_odds_1, away_odds_2, price_total, odds_over, odds_under) values ('{}', '{}', '{}', '{}', '{}', {}, {}, {}, {}, {}, {}, {});"
time_key = '(\d+)\:(\d+)([ap])'
games_date_key = '.+?\,\s+(\S+)\s+(\d+)[thndr]{2}\s+at\s+(\d+)\:(\d+)([ap])m'
odds_date_key = '(\D+) (\d+). (\d+)\s+(\d+)\:(\d+) ([AP])'
months = 'January February March April May June July August September October November December'.split()

# variables
driver = None
database = None
cursor = None

# helper
def wait_for_element(class_name, by=By.CLASS_NAME):
	WebDriverWait(driver, element_timeout).until(EC.presence_of_element_located((by, class_name)))

def query (qu, *args):
	cursor.execute(qu.format(*args))
	database.commit()

def numstr(value):
	val = int(value)
	if val < 10: return '0' + str(val)
	else: return str(val)

# main
if __name__ == '__main__':

	# log into database
	database = pymysql.connect(**json.load(open('database.json')))
	cursor = database.cursor()

	# start driver
	driver_options = webdriver.firefox.options.Options()
	driver_options.headless = False
	driver = webdriver.Firefox('geckodriver', options=driver_options)
	
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

	table = driver.find_element_by_tag_name('table')
	cells = table.text.split('\n')
	row = []
	for cell in cells[best_bets_column_count:]:
		row.append(cell)
		if len(row) > best_bets_column_count:

			# prepare for error
			try:

				# fix date and time
				datestr = row.pop(2)
				month, day = (int(item) for item in datestr.split('/'))
				if month < today.month: year = today.year + 1
				else: year = today.year
				hour, minute, apm = re.findall(time_key, row[2])[0]
				hour = int(hour)
				if apm == 'p': hour += 12
				if hour == 24: hour = 0
				minute = int(minute)
				row[2] = '{}-{}-{} {}:{}:00'.format(
					year, numstr(month), numstr(day),
					numstr(hour), numstr(minute),
				)

				# clean up
				row[7] = row[7][1:]

				# store
				query(bestbets_insert, *row)

				# reset
				row = []
			# oops
			except:pass

	# go to sports
	#for sport, uses_calendar in (('NFL', False), ('NCAAF', False), ('NBA', True), ('NCAAB', True), ('MLB', True), ('NHL', True)):
	for sport, uses_calendar in (('NBA', True), ('NCAAB', True), ('MLB', True), ('NHL', True)):

		# initalize games page
		driver.get(initial_games_url.format(sport.lower()))
		wait_for_element(games_table_class)

		# get games data
		last_url = ''
		if uses_calendar: week = today
		else: week = 1
		while True:

			# go to page
			driver.get(games_url.format(sport.lower(), week))
			try:
				wait_for_element(games_table_class)
				if driver.current_url == last_url: break

				# go through tables
				for table in driver.find_elements_by_class_name(games_table_class):

					# prepare for error
					try:

						# start
						data = htt(table.get_attribute('innerHTML')).split('\n')

						# format time
						month, day, hour, minute, apm = re.findall(games_date_key, data[14])[0]
						month_num = months.index(month) + 1
						year = today.year
						if month_num < 9: year += 1
						hour = int(hour)
						if apm == 'p': hour += 12
						if hour == 24: hour = 0

						# store data
						query(games_insert,
							sport,
							data[10].strip() + ' ' + data[12].strip(),
							data[0].strip() + ' ' + data[2].strip(),
							'{}-{}-{} {}:{}:00'.format(year, numstr(month_num), numstr(day), numstr(hour), numstr(minute)),
							data[24].replace('%', ''), data[16].replace('%', ''),
							data[34], data[26],
							data[46], data[54][1:], data[50], data[36][1:], data[40],
							data[66], data[74][1:], data[70][:len(data[70]) - 3], data[56][1:], data[60][:len(data[60]) - 3]
						)

					# oops
					except:pass

			# oops
			except TimeoutException:
				if driver.current_url == last_url: break
			except NoSuchElementException:
				if driver.current_url == last_url: break

			# update
			if uses_calendar: week -= datetime.timedelta(days=1)
			else: week += 1
			last_url = driver.current_url


		# get odds data
		driver.get(odds_url.format(sport.lower()))
		wait_for_element(odds_table_class)
		for table in driver.find_elements_by_class_name(odds_table_class):

			# prepare for error
			try:

				# start
				row = {'league': sport}

				# date / time
				data_cell = driver.find_element_by_class_name('chalk-cell.chalk-cell-date')
				month, day, year, hour, minute, apm = re.findall(odds_date_key, data_cell.text, re.DOTALL)[0]
				hour = int(hour)
				if apm == 'P': hour += 12
				if hour == 24: hour = 0
				if hour == 24: hour = 0
				row['date'] = '{}-{}-{} {}:{}:00'.format(
					year, numstr(months.index(month) + 1), day,
					hour, minute
				)

				# team names
				cell = driver.find_element_by_class_name('chalk-cell.chalk-team.chalk-team-away')
				if cell: row['away'] = cell.text.strip()

				cell = driver.find_element_by_class_name('chalk-cell.chalk-team.chalk-team-home')
				if cell: row['home'] = cell.text.strip()

				# odds
				row['odds'] = {}
				for odds_table in table.find_elements_by_class_name('chalk-odds-scroller'):
					for column in odds_table.find_elements_by_tag_name('td'):

						column_name = column.find_element_by_class_name('chalk-cell.chalk-header').text.strip()
						row['odds'][column_name] = {}

						for class_id, name in (
								('chalk-cell.chalk-odds.chalk-odds-away', 'away-odds'),
								('chalk-cell.chalk-odds.chalk-odds-home', 'home-odds'),
								('chalk-price.chalk-price-total', 'price-total'),
								('chalk-price.chalk-price-overunder', 'overunder'),
						):
							cell = column.find_element_by_class_name(class_id)
							if cell: row['odds'][column_name][name] = cell.text.strip()
							else: row['odds'][column_name][name] = ''

				# save data
				for odds in row['odds']:

					if row['odds'][odds]['home-odds']:
						value = row['odds'][odds]['home-odds'].strip().split()
						if len(value) == 1: home_odds = (float(value), 0)
						else: home_odds = tuple(float(item) for item in value)
					else: home_odds = (0, 0)

					if row['odds'][odds]['away-odds']:
						value = row['odds'][odds]['away-odds'].strip().split()
						if len(value) == 1: away_odds = (float(value), 0)
						else: away_odds = tuple(float(item) for item in value)
					else: away_odds = (0, 0)

					overunder = row['odds'][odds]['overunder'].split('\n')

					query(odds_insert,
						  sport,
						  row['home'], row['away'],
						  row['date'],
						  odds, home_odds[0], home_odds[1], away_odds[0], away_odds[1],
						  row['odds'][odds]['price-total'],
						  overunder[0][1:], overunder[1][1:],
					)

			# oops
			except:pass
