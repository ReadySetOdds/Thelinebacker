
# import dependencies
from selenium import webdriver

# settings
username = 'rmarshallsmith@hotmail.com'
password = 'football2020'
signin_url = 'https://www.thelinebacker.com/signin'
games_url = 'https://www.thelinebacker.com/{}/games/{}'
odds_url = 'https://www.thelinebacker.com/odds/{}'
best_bets_column_count = 8

# variables
driver = None

# main
if __name__ == '__main__':
	
	# start driver
	driver = webdriver.Firefox()
	
	# log into page
	driver.get(signin_url)
	for element in driver.find_elements_by_tag_name('input'):
		name = element.get_attribute('name')
		if name == 'email':
			element.send_keys(username)
		elif name == 'password':
			element.send_keys(password)
	for element in driver.find_elements_by_tag_name('button'):
		if element.text == 'Log in':
			element.click()
			break
	
	# get best bets
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
		if len(row) > best_bets_column_count: pass
	
	'''
	# go to sports
	for sport in ('NFL', 'NCAAF', 'NBA', 'NCAAB', 'MLB', 'NHL'):
		
		# games
		page_number = 1
		while True:
			driver.get(games_url.format(sport, page_number))
			for element in driver.find_elements_by_tag_name('tbody'):
				for child in element.find_elements_by_tag_name('td'):
					print(child.find_attribute('data-cy'))
			exit()
	'''
