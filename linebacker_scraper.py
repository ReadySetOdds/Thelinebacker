
# import dependencies
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from html2text import html2text as htt
import pymysql.cursors
import json, datetime, re, os, pickle, sys, inspect, requests, time
from bs4 import BeautifulSoup

# constants
script_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))).replace('\\', '/')
linebacker_username = 'rmarshallsmith@hotmail.com'
linebacker_password = 'football2020'
signin_url = 'https://www.predictionmachine.com/signin'
initial_games_url = 'https://www.predictionmachine.com/{}/games'
games_url = initial_games_url + '/{}'
odds_url = 'https://www.predictionmachine.com/odds/{}'
best_bets_column_count = 8
element_timeout = 20
calendar_button = 'sc-feWbDf bVBUqB.sc-htoDjs iArBBn'
weeks_dropdown_button_class = 'sc-keVrkP ktOnIp'
weeks_dropdown_list_class = 'sc-exkUMo hyEDPn'
games_table_class = 'sc-fjhmcy.blYQRy'
odds_table_class = 'chalk-event'
table_indices = (0, 2, 10, 12, 16, 18, 26, 28, 36, 38, 44, 48, 50, 56, 60)
best_bets_table_id = 'sc-bTiqRo LaLZW'
bestbets_insert = "INSERT IGNORE INTO bestbets (rotation, league, date, match_details, play, line, odds, play_amount) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
games_insert = "INSERT IGNORE INTO games (league, home_team, away_team, date, home_win, away_win, home_proj_score, away_proj_score, spread_total, home_spread_1, home_spread_2, away_spread_1, away_spread_2, total, home_total, odds_under, away_total, odds_total) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
odds_insert = "INSERT IGNORE INTO odds (league, home_team, away_team, date, odds_group, home_odds_1, home_odds_2, away_odds_1, away_odds_2, price_total, odds_over, odds_under) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
time_key = '(\d+)\:(\d+)([ap])'
games_date_key = '.+?\,\s+(\S+)\s+(\d+)[thndr]{2}\s+at\s+(\d+)\:(\d+)([ap])m'
odds_date_key = '(\D+) (\d+). (\d+)\s+(\d+)\:(\d+) ([AP])'
months = 'January February March April May June July August September October November December'.split()
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15"}


# variables
driver = None
database = None
database_on = True
cursor = None

# helper
def wait_for_element(class_name, by=By.CLASS_NAME):
	WebDriverWait(driver, element_timeout).until(EC.presence_of_element_located((by, class_name)))

# def query (qu, args):
# 	if database_on:
# 		args = tuple(args)
# 		cursor.execute(qu, args)
# 		database.commit()
# 		print(cursor.rowcount, "record inserted.")
# 	else: print(args)

def numstr(value):
	val = int(value)
	if val < 10: return '0' + str(val)
	else: return str(val)


def convert(seconds):
    return time.strftime("%H:%M:%S", time.gmtime(seconds))

# main
if __name__ == '__main__':
	while True:
		print('Start')
		# get lasts
		# if os.path.exists('already.pkl'):
		if False:
			already = pickle.load(open(script_path + '/already.pkl', 'rb'))
		else:
			already = {name:{sport: [] for sport in ('NFL','NCAAF', 'NBA', 'NCAAB', 'MLB', 'NHL')} for name in ('odds', 'games')}
			already['bestbets'] = []

		# scrape all pages or just 1
		do_all = False
		if len(sys.argv) > 1:
			if 'all' in sys.argv: do_all = True

		# log into database
		if database_on:
			database = pymysql.connect(**json.load(open(script_path + '/database.json')))
			cursor = database.cursor()
			print(database)
		

		# start driver
		# driver_options = webdriver.firefox.options.Options()
		# driver_options.headless = True
		# driver = webdriver.Firefox(options=driver_options)
		# driver_options = webdriver.ChromeOptions()
		# driver_options.add_argument('headless')
		# driver_options.add_argument('window-size=1200x600')
		# driver = webdriver.Chrome(chrome_options=driver_options)
		driver = webdriver.PhantomJS()
		driver.set_window_size(1120, 550)

		# log into page
		driver.get(signin_url)
		for element in driver.find_elements_by_tag_name('input'):
			name = element.get_attribute('name')
			if name == 'email':
				element.send_keys('rmarshallsmith@hotmail.com')
			elif name == 'password':
				element.send_keys('football2020')
		for element in driver.find_elements_by_tag_name('button'):
			if element.get_attribute('data-cy') == 'signin-submit':
				element.click()
				break


		# get best bets
		today = datetime.date.today()
		if today not in already['bestbets']:
			already['bestbets'].append(today)
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
						if month < 1: year = today.year - 1
						else: year = today.year
						hour, minute, apm = re.findall(time_key, row[2])[0]
						hour = int(hour) + 1
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
						data = tuple(row)
						cursor.execute(bestbets_insert, data)
						database.commit()
						print(row)

						# reset
						row = []
					# oops
					except:pass

		# go to sports
		sport_did = []
		for sport, uses_calendar, special_odds in (
				('NFL', False, False), ('NCAAF', False, False),
				('NBA', True, False), ('NCAAB', True, False),
				('MLB', True, True), ('NHL', True, False)
		):
			do_this = True
			if True:

				# initialize games page
				# driver.get(initial_games_url.format(sport.lower()))
				# print(initial_games_url.format(sport.lower()))

				try:
					# wait_for_element(games_table_class)
					# for element in driver.find_elements_by_tag_name('div'):
					# 	print(element.get_attribute('class'))


					# get games data
					last_url = ''
					if uses_calendar: week = today
					else: week = ''
					if True:

						# do this
						if do_all:
							do_this = True
						else:
							if sport in sport_did: 
								do_this = False
							else:
								do_this = True
								sport_did.append(sport)
						if do_this:

							# start
							if week not in already['games'][sport]:
								already['games'][sport].append(week)

								# go to page
								driver.get(games_url.format(sport.lower(), week))
								print(games_url.format(sport.lower(), week))


								try:

									wait_for_element('table', By.TAG_NAME)
									if driver.current_url == last_url: break

									games_index = []
									games_number = 0
									Month = []
									Day = []
									Hour = []
									Minute = []
									Apm = []
									start = 0
									game_table = []


									# go through tables
									for table in driver.find_elements_by_tag_name('table'):
										if(table.get_attribute('class') == "sc-fjhmcy blYQRy"):
											# prepare for error
											try:

												# start
												data = htt(table.get_attribute('innerHTML')).split('\n')
												game_table.append(data)

												if(len(data) > 3):
													special_odds = False
												else:
													special_odds = not special_odds


												# for i in range(0,len(data)):
												# 	if("vs" in data[i]):
												# 		games_index.append(len(data))
												
												for i in data:
													if(", " in i and " at " in i and "am" in i or "pm" in i):
														# format time
														month, day, hour, minute, apm = re.findall(games_date_key, i)[0]
														month_num = months.index(month) + 1
														year = today.year
														if month_num < 1:
															year -= 1
														hour = int(hour) + 1
														if apm == 'p':
															hour += 12
														if hour >= 24:
															hour -= 24
														Month.append(month_num)
														Day.append(day)
														Hour.append(hour)
														Minute.append(minute)
														Apm.append(apm)
														
												# for p in range(0,len(games_index)):
												# 	game_table.append(data)
													# start = games_index[p]
												

											# oops
											except:pass
									
									result = []
									data2 = ()
									for n in range(0,len(game_table)):
										if(len(game_table[n]) == 79):
											result = []
											data2 = ()
											result.append(sport)
											# print(game_table[n][10].strip() + ' ' + game_table[n][12].strip())
											result.append(game_table[n][10].strip() + ' ' + game_table[n][12].strip())
											# print(game_table[n][0].strip() + ' ' + game_table[n][2].strip())
											result.append(game_table[n][0].strip() + ' ' + game_table[n][2].strip())
											# print('{}-{}-{} {}: {}: 00'.format(year, numstr(Month[n]), numstr(Day[n]), numstr(Hour[n]), numstr(Minute[n])))
											result.append('{}-{}-{} {}: {}: 00'.format(year, numstr(Month[n]), numstr(Day[n]), numstr(Hour[n]), numstr(Minute[n])))
											temp = (game_table[n][24].replace('%', '') + game_table[n][16].replace('%', '')).replace('|', '')
											# print(temp)
											temp = (game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][22].strip() + " " + game_table[n][26].strip())
											# print(temp)
											result.append(game_table[n][24].strip())
											temp = (game_table[n][0].strip() + ' ' + game_table[n][2].strip() + " " + game_table[n][22].strip() + " " + game_table[n][18].strip())
											# print(temp)
											result.append(game_table[n][16].strip())
											temp = game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][32].strip() + " " + game_table[n][36].strip()
											# print(temp)
											result.append(game_table[n][34].strip())
											temp = game_table[n][0].strip() + ' ' + game_table[n][2].strip() + " " + game_table[n][32].strip() + " " + game_table[n][28].strip()
											# print(temp)
											result.append(game_table[n][26].strip())
											temp = game_table[n][46].strip() + " " + game_table[n][48].strip()
											# print(temp)
											result.append(game_table[n][46].strip())
											temp = game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][46].strip() + " " + game_table[n][38].strip() + " " + game_table[n][42].strip()
											# print(temp)
											result.append(game_table[n][54].strip())
											result.append(game_table[n][50].strip())
											temp = game_table[n][0].strip() + ' ' + game_table[n][2].strip() + " " + game_table[n][46].strip() + " " + game_table[n][56].strip() + " " + game_table[n][52].strip()
											# print(temp)
											result.append(game_table[n][36].strip())
											result.append(game_table[n][40].strip())
											temp = game_table[n][66].strip() + " " + game_table[n][68].strip()
											# print(tem
											result.append(game_table[n][66].strip())
											temp = game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][66].strip() + game_table[n][76].strip() + " " + game_table[n][72].strip()
											# print(temp)
											result.append(game_table[n][74].strip())
											result.append(game_table[n][70].strip())
											temp = game_table[n][0].strip() + ' ' + game_table[n][2].strip() + " " + game_table[n][66].strip() + game_table[n][58].strip() + " " + game_table[n][62].strip()
											# print(temp)
											result.append(game_table[n][56].strip())
											result.append(game_table[n][60].strip())

											data2 = tuple(result)
											print(data2)
											cursor.execute(games_insert, data2)
											print(cursor.rowcount, "record inserted.")
											print("from 1")
											database.commit()
											# print('\n')
										elif(len(game_table[n]) == 87):
											result = []
											data2 = ()
											result.append(sport)
											# print(game_table[n][10].strip() + ' ' + game_table[n][12].strip())
											result.append(game_table[n][10].strip() + ' ' + game_table[n][12].strip())
											# print(game_table[n][0].strip() + ' ' + game_table[n][2].strip())
											result.append(game_table[n][0].strip() + ' ' + game_table[n][2].strip())
											# print('{}-{}-{} {}: {}: 00'.format(year, numstr(Month[n]), numstr(Day[n]), numstr(Hour[n]), numstr(Minute[n])))
											result.append('{}-{}-{} {}: {}: 00'.format(year, numstr(Month[n]), numstr(Day[n]), numstr(Hour[n]), numstr(Minute[n])))
											# date
											temp = (game_table[n][24].replace('%', '') + game_table[n][16].replace('%', '')).replace('|', '')
											# print(temp)
											# Pitcher
											temp = (game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][12].strip() + " " + game_table[n][22].strip() + " " + game_table[n][26].strip())
											# print(temp)
											temp = (game_table[n][0].strip() + ' ' + game_table[n][2].strip() + " " + game_table[n][12].strip() + " " + game_table[n][22].strip() + " " + game_table[n][18].strip())
											# print(temp)
											# Win %
											temp = game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][32].strip() + " " + game_table[n][36].strip()
											# print(temp)
											result.append(game_table[n][34].strip())
											temp = game_table[n][0].strip() + ' ' + game_table[n][2].strip() + " " + game_table[n][32].strip() + " " + game_table[n][28].strip()
											# print(temp)
											result.append(game_table[n][26].strip())
											# Proj Score
											temp = game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][42].strip() + " " + game_table[n][38].strip()
											# print(temp)
											result.append(game_table[n][44].strip())
											temp = game_table[n][0].strip() + ' ' + game_table[n][2].strip() + " " + game_table[n][42].strip() + " " + game_table[n][46].strip()
											# print(temp)
											result.append(game_table[n][36].strip())
											# Money Line
											result.append("N/A")
											temp = game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][56].strip() + game_table[n][64].strip() + " " + game_table[n][60].strip()
											# print(temp)
											result.append(game_table[n][62].strip())
											result.append(game_table[n][58].strip())
											temp = game_table[n][0].strip() + ' ' + game_table[n][2].strip() + " " + game_table[n][56].strip() + game_table[n][48].strip() + " " + game_table[n][52].strip()
											# print(temp)
											result.append(game_table[n][46].strip())
											result.append(game_table[n][50].strip())
											# Total
											temp = game_table[n][74].strip() + " " + game_table[n][76].strip()
											# print(temp)
											result.append(game_table[n][74].strip())
											temp = game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][74].strip() + " " + game_table[n][84].strip() + " " + game_table[n][80].strip()
											# print(temp)
											result.append(game_table[n][82].strip())
											result.append(game_table[n][78].strip())
											temp = game_table[n][0].strip() + ' ' + game_table[n][2].strip() + " " + game_table[n][74].strip() + " " + game_table[n][66].strip() + " " + game_table[n][70].strip()
											# print(temp)
											result.append(game_table[n][64].strip())
											result.append(game_table[n][68].strip())
											
											data2 = tuple(result)
											print(data2)
											cursor.execute(games_insert, data2)
											print(cursor.rowcount, "record inserted.")
											print("from 2")
											database.commit()
											# print('\n')
										elif(len(game_table[n]) == 65):
											result = []
											data2 = ()
											result.append(sport)
											# print(game_table[n][10].strip() + ' ' + game_table[n][12].strip())
											result.append(game_table[n][10].strip() + ' ' + game_table[n][12].strip())
											# print(game_table[n][0].strip() + ' ' + game_table[n][2].strip())
											result.append(game_table[n][0].strip() + ' ' + game_table[n][2].strip())
											# print('{}-{}-{} {}: {}: 00'.format(year, numstr(Month[n]), numstr(Day[n]), numstr(Hour[n]), numstr(Minute[n])))
											result.append('{}-{}-{} {}: {}: 00'.format(year, numstr(Month[n]), numstr(Day[n]), numstr(Hour[n]), numstr(Minute[n])))
											# date
											temp = (game_table[n][24].replace('%', '') + game_table[n][16].replace('%', '')).replace('|', '')
											# print(temp)
											# Pitcher
											temp = (game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][12].strip() + " " + game_table[n][22].strip() + " " + game_table[n][26].strip())
											# print(temp)
											temp = (game_table[n][0].strip() + ' ' + game_table[n][2].strip() + " " + game_table[n][12].strip() + " " + game_table[n][22].strip() + " " + game_table[n][18].strip())
											# print(temp)
											# Win %
											temp = game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][32].strip() + " " + game_table[n][36].strip()
											# print(temp)
											result.append(game_table[n][34].strip())
											temp = game_table[n][0].strip() + ' ' + game_table[n][2].strip() + " " + game_table[n][32].strip() + " " + game_table[n][28].strip()
											# print(temp)
											result.append(game_table[n][26].strip())
											# Proj Score
											temp = game_table[n][0].strip() + ' ' + game_table[n][2].strip() + " " + game_table[n][42].strip() + " " + game_table[n][38].strip()
											# print(temp)
											result.append(game_table[n][44].strip())
											temp = game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][42].strip() + " " + game_table[n][46].strip()
											# print(temp)
											result.append(game_table[n][36].strip())
											# Money Line
											temp = game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][54].strip() + " " + game_table[n][60].strip()
											# print(temp)
											result.append(game_table[n][62].strip())
											result.append(game_table[n][58].strip())
											temp = game_table[n][0].strip() + ' ' + game_table[n][2].strip() + " " + game_table[n][54].strip() + " " + game_table[n][48].strip()
											# print(temp)
											result.append(game_table[n][46].strip())
											result.append(game_table[n][50].strip())
											# Total
											result.append("N/A")
											temp = game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][68].strip() + " " + game_table[n][62].strip()
											# print(temp)
											result.append("N/A")
											result.append("N/A")
											temp = game_table[n][10].strip() + ' ' + game_table[n][12].strip() + " " + game_table[n][68].strip() + " " + game_table[n][74].strip()
											# print(temp)
											result.append("N/A")
											result.append("N/A")
											
											data2 = tuple(result)
											print(data2)
											cursor.execute(games_insert, data2)
											print(cursor.rowcount, "record inserted.")
											print("from 3")
											database.commit()
											print('\n')



								# oops
								except TimeoutException:
									if driver.current_url == last_url: break
								except NoSuchElementException:
									if driver.current_url == last_url: break

								# update
								if uses_calendar: week -= datetime.timedelta(days=1)
								else: week += 1
								last_url = driver.current_url
						else: break
				# oops
				except: 
					pass
				
				try:
					# get odds data
					if not special_odds and do_this:
						driver.get(odds_url.format(sport.lower()))
						print(odds_url.format(sport.lower()))
						wait_for_element(odds_table_class)

						count = -1
						odds_group = ['Caesars', 'Wynn', 'Station', 'Mirage', 'Westgate']

						for table in driver.find_elements_by_class_name(odds_table_class):
							try:
								Caesars = False
								Wynn = False
								Station = False
								Mirage = False
								Westgate = False
								count += 1

								# odds
								if today not in already['odds'][sport]:
									already['odds'][sport].append(sport)

									# prepare for error
									try:

										# start
										row = {'league': sport}
										data = htt(table.get_attribute('innerHTML')).split('\n')

										print(data)
										print(len(data))
										print('\n')

										date = data[2] + data[3]
										month, day, year, hour, minute, apm = re.findall(odds_date_key, date, re.DOTALL)[0]
										hour = int(hour) + 1
										if apm == 'P': hour += 12
										if hour == 24: hour = 0
										row['date'] = '{}-{}-{} {}:{}:00'.format(year, numstr(months.index(month) + 1), day, hour, minute)

										# Home Team
										row['home'] = data[11]
										# Away Team
										row['away'] = data[9]

										# Odds Group
										odds_group_count = 0
										for m in data:
											if(m.strip() == odds_group[0]):Caesars=True
											elif(m.strip() == odds_group[1]):Wynn=True
											elif(m.strip() == odds_group[2]):Station=True
											elif(m.strip() == odds_group[3]):Mirage=True
											elif(m.strip() == odds_group[4]):Westgate=True

										if Caesars:
											row['odds_group'] = 'Caesars'
											# home
											row['home_odds_1'] = data[data.index('Caesars')+4].strip().split(" ")[0]
											row['home_odds_2'] = data[data.index('Caesars')+4].strip().split(" ")[-1]
											# away
											row['away_odds_1'] = data[data.index('Caesars')+2].strip().split(" ")[0]
											row['away_odds_2'] = data[data.index('Caesars')+2].strip().split(" ")[-1]
											# price_total
											row['price_total'] = data[data.index('Caesars')+6]
											# odds over
											row['odds_over'] = data[data.index('Caesars')+6+2]
											# odds under
											row['odds_under'] = data[data.index('Caesars')+6+2+1]
											# sent to the database
											result = []
											result.append(sport)
											result.append(row['home'])
											result.append(row['away'])
											result.append(row['date'])
											if(row['odds_group'] == ''):result.append('N/A')
											else:result.append(row['odds_group'])
											if(row['home_odds_1'] == ''):result.append('N/A')
											else:result.append(row['home_odds_1'])
											if(row['home_odds_2'] == ''):result.append('N/A')
											else:result.append(row['home_odds_2'])
											if(row['away_odds_1'] == ''):result.append('N/A')
											else:result.append(row['away_odds_1'])
											if(row['away_odds_2'] == ''):result.append('N/A')
											else:result.append(row['away_odds_2'])
											if(row['price_total'] == ''):result.append('N/A')
											else:result.append(row['price_total'])
											if(row['odds_over'] == ''):result.append('N/A')
											else:result.append(row['odds_over'])
											if(row['odds_under'] == ''):result.append('N/A')
											else:result.append(row['odds_under'])

											data3 = tuple(result)
											print(data3)
											cursor.execute(odds_insert, data3)
											print(cursor.rowcount, "record inserted.")
											database.commit()
										if Wynn:
											row['odds_group'] = 'Wynn'
											# home
											row['home_odds_1'] = data[data.index('Caesars')+4].strip().split(" ")[0]
											row['home_odds_2'] = data[data.index('Caesars')+4].strip().split(" ")[-1]
											# away
											row['away_odds_1'] = data[data.index('Caesars')+2].strip().split(" ")[0]
											row['away_odds_2'] = data[data.index('Caesars')+2].strip().split(" ")[-1]
											# price_total
											row['price_total'] = data[data.index('Caesars')+6]
											# odds over
											row['odds_over'] = data[data.index('Caesars')+6+2]
											# odds under
											row['odds_under'] = data[data.index('Caesars')+6+2+1]
											# sent to the database
											result = []
											result.append(sport)
											result.append(row['home'])
											result.append(row['away'])
											result.append(row['date'])
											if(row['odds_group'] == ''):result.append('N/A')
											else:result.append(row['odds_group'])
											if(row['home_odds_1'] == ''):result.append('N/A')
											else:result.append(row['home_odds_1'])
											if(row['home_odds_2'] == ''):result.append('N/A')
											else:result.append(row['home_odds_2'])
											if(row['away_odds_1'] == ''):result.append('N/A')
											else:result.append(row['away_odds_1'])
											if(row['away_odds_2'] == ''):result.append('N/A')
											else:result.append(row['away_odds_2'])
											if(row['price_total'] == ''):result.append('N/A')
											else:result.append(row['price_total'])
											if(row['odds_over'] == ''):result.append('N/A')
											else:result.append(row['odds_over'])
											if(row['odds_under'] == ''):result.append('N/A')
											else:result.append(row['odds_under'])

											data3 = tuple(result)
											print(data3)
											cursor.execute(odds_insert, data3)
											print(cursor.rowcount, "record inserted.")
											database.commit()
										if Station:
											row['odds_group'] = 'Station'
											# home
											row['home_odds_1'] = data[data.index('Caesars')+4].strip().split(" ")[0]
											row['home_odds_2'] = data[data.index('Caesars')+4].strip().split(" ")[-1]
											# away
											row['away_odds_1'] = data[data.index('Caesars')+2].strip().split(" ")[0]
											row['away_odds_2'] = data[data.index('Caesars')+2].strip().split(" ")[-1]
											# price_total
											row['price_total'] = data[data.index('Caesars')+6]
											# odds over
											row['odds_over'] = data[data.index('Caesars')+6+2]
											# odds under
											row['odds_under'] = data[data.index('Caesars')+6+2+1]
											# sent to the database
											result = []
											result.append(sport)
											result.append(row['home'])
											result.append(row['away'])
											result.append(row['date'])
											if(row['odds_group'] == ''):result.append('N/A')
											else:result.append(row['odds_group'])
											if(row['home_odds_1'] == ''):result.append('N/A')
											else:result.append(row['home_odds_1'])
											if(row['home_odds_2'] == ''):result.append('N/A')
											else:result.append(row['home_odds_2'])
											if(row['away_odds_1'] == ''):result.append('N/A')
											else:result.append(row['away_odds_1'])
											if(row['away_odds_2'] == ''):result.append('N/A')
											else:result.append(row['away_odds_2'])
											if(row['price_total'] == ''):result.append('N/A')
											else:result.append(row['price_total'])
											if(row['odds_over'] == ''):result.append('N/A')
											else:result.append(row['odds_over'])
											if(row['odds_under'] == ''):result.append('N/A')
											else:result.append(row['odds_under'])

											data3 = tuple(result)
											print(data3)
											cursor.execute(odds_insert, data3)
											print(cursor.rowcount, "record inserted.")
											database.commit()
										if Mirage:
											row['odds_group'] = 'Mirage'
											# home
											row['home_odds_1'] = data[data.index('Caesars')+4].strip().split(" ")[0]
											row['home_odds_2'] = data[data.index('Caesars')+4].strip().split(" ")[-1]
											# away
											row['away_odds_1'] = data[data.index('Caesars')+2].strip().split(" ")[0]
											row['away_odds_2'] = data[data.index('Caesars')+2].strip().split(" ")[-1]
											# price_total
											row['price_total'] = data[data.index('Caesars')+6]
											# odds over
											row['odds_over'] = data[data.index('Caesars')+6+2]
											# odds under
											row['odds_under'] = data[data.index('Caesars')+6+2+1]
											# sent to the database
											result = []
											result.append(sport)
											result.append(row['home'])
											result.append(row['away'])
											result.append(row['date'])
											if(row['odds_group'] == ''):result.append('N/A')
											else:result.append(row['odds_group'])
											if(row['home_odds_1'] == ''):result.append('N/A')
											else:result.append(row['home_odds_1'])
											if(row['home_odds_2'] == ''):result.append('N/A')
											else:result.append(row['home_odds_2'])
											if(row['away_odds_1'] == ''):result.append('N/A')
											else:result.append(row['away_odds_1'])
											if(row['away_odds_2'] == ''):result.append('N/A')
											else:result.append(row['away_odds_2'])
											if(row['price_total'] == ''):result.append('N/A')
											else:result.append(row['price_total'])
											if(row['odds_over'] == ''):result.append('N/A')
											else:result.append(row['odds_over'])
											if(row['odds_under'] == ''):result.append('N/A')
											else:result.append(row['odds_under'])

											data3 = tuple(result)
											print(data3)
											cursor.execute(odds_insert, data3)
											print(cursor.rowcount, "record inserted.")
											database.commit()
										if Westgate:
											row['odds_group'] = 'Westgate'
											# home
											row['home_odds_1'] = data[data.index('Caesars')+4].strip().split(" ")[0]
											row['home_odds_2'] = data[data.index('Caesars')+4].strip().split(" ")[-1]
											# away
											row['away_odds_1'] = data[data.index('Caesars')+2].strip().split(" ")[0]
											row['away_odds_2'] = data[data.index('Caesars')+2].strip().split(" ")[-1]
											# price_total
											row['price_total'] = data[data.index('Caesars')+6]
											# odds over
											row['odds_over'] = data[data.index('Caesars')+6+2]
											# odds under
											row['odds_under'] = data[data.index('Caesars')+6+2+1]
											# sent to the database
											result = []
											result.append(sport)
											result.append(row['home'])
											result.append(row['away'])
											result.append(row['date'])
											if(row['odds_group'] == ''):result.append('N/A')
											else:result.append(row['odds_group'])
											if(row['home_odds_1'] == ''):result.append('N/A')
											else:result.append(row['home_odds_1'])
											if(row['home_odds_2'] == ''):result.append('N/A')
											else:result.append(row['home_odds_2'])
											if(row['away_odds_1'] == ''):result.append('N/A')
											else:result.append(row['away_odds_1'])
											if(row['away_odds_2'] == ''):result.append('N/A')
											else:result.append(row['away_odds_2'])
											if(row['price_total'] == ''):result.append('N/A')
											else:result.append(row['price_total'])
											if(row['odds_over'] == ''):result.append('N/A')
											else:result.append(row['odds_over'])
											if(row['odds_under'] == ''):result.append('N/A')
											else:result.append(row['odds_under'])

											data3 = tuple(result)
											print(data3)
											cursor.execute(odds_insert, data3)
											print(cursor.rowcount, "record inserted.")
											database.commit()

											# date / time
											# data_cell = driver.find_elements_by_class_name('chalk-cell.chalk-cell-date')[count]
											# month, day, year, hour, minute, apm = re.findall(odds_date_key, data_cell.text, re.DOTALL)[0]
											# hour = int(hour) + 1
											# if apm == 'P': hour += 12
											# if hour == 24: hour = 0
											# row['date'] = '{}-{}-{} {}:{}:00'.format(year, numstr(months.index(month) + 1), day, hour, minute)

											# # team names
											# cell = driver.find_elements_by_class_name('chalk-cell.chalk-team.chalk-team-away')[count]
											# if cell: row['away'] = cell.text.strip()

											# cell = driver.find_elements_by_class_name('chalk-cell.chalk-team.chalk-team-home')[count]
											# if cell: row['home'] = cell.text.strip()
											# print(row)

											# # odds
											# row['odds'] = {}
											# for odds_table in table.find_elements_by_class_name('chalk-odds-wrapper'):
											# 	for column in odds_table.find_elements_by_tag_name('td'):

											# 		column_name = column.find_element_by_class_name('chalk-cell chalk-header').text.strip()
											# 		row['odds'][column_name] = {}

											# 		for class_id, name in (
											# 				('chalk-cell chalk-odds chalk-odds-away', 'away-odds'),
											# 				('chalk-cell chalk-odds chalk-odds-home', 'home-odds'),
											# 				('chalk-price chalk-price-total', 'price-total'),
											# 				('chalk-price chalk-price-overunder', 'overunder'),
											# 		):
											# 			cell = column.find_element_by_class_name(class_id)
											# 			if cell: row['odds'][column_name][name] = cell.text.strip()
											# 			else: row['odds'][column_name][name] = ''

											# # # save data
											# for odds in row['odds']:

											# 	if row['odds'][odds]['home-odds']:
											# 		value = row['odds'][odds]['home-odds'].strip().split()
											# 		if len(value) == 1: home_odds = (float(value[0]), 0)
											# 		else: home_odds = tuple(float(item) for item in value)
											# 	else: 
											# 		home_odds = (0, 0)

											# 	if row['odds'][odds]['away-odds']:
											# 		value = row['odds'][odds]['away-odds'].strip().split()
											# 		if len(value) == 1: away_odds = (float(value[0]), 0)
											# 		else: away_odds = tuple(float(item) for item in value)
											# 	else: away_odds = (0, 0)
											

											# 	overunder = row['odds'][odds]['overunder'].split('\n')

											# 	# query(odds_insert,
											# 	# 	  sport,
											# 	# 	  row['home'], row['away'],
											# 	# 	  row['date'],
											# 	# 	  odds, home_odds[0], home_odds[1], away_odds[0], away_odds[1],
											# 	# 	  row['odds'][odds]['price-total'],
											# 	# 	  overunder[0][1:], overunder[1][1:],
											# 	# )
											# 	result2 = []
											# 	result2.append(sport)
											# 	result2.append(row['home'])
											# 	result2.append(row['away'])
											# 	result2.append(row['date'])
											# 	result2.append(odds)
											# 	result2.append(home_odds[0])
											# 	result2.append(home_odds[1])
											# 	result2.append(away_odds[0])
											# 	result2.append(away_odds[1])
											# 	result2.append(row['odds'][odds]['price-total'])
											# 	result2.append(overunder[0][1:])
											# 	result2.append(overunder[1][1:])

											# 	data3 = tuple(result2)
											# 	print(data3)
											# 	cursor.execute(odds_insert, data3)
											# 	print(cursor.rowcount, "record inserted.")
											# 	database.commit()

												# try:
												# 	print(row['home'], row['away'])
												# 	print(row['date'])
												# 	print(odds, home_odds[0], home_odds[1], away_odds[0], away_odds[1])
												# 	print(row['odds'][odds]['price-total'])
												# 	print(overunder[0][1:], overunder[1][1:])
												# except:
												# 	continue
										else:
											pass

									# oops
									except:pass
							except:pass
				except:pass
									

		# finished
		driver.close()
		pickle.dump(already, open(script_path + '/already.pkl', 'wb'))
		print('Finished!')
		for h in range(0, 21599):
			time.sleep(1)
			print(convert(h))

