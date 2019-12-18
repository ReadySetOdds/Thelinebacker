
# import dependencies
import pymysql, json

# main
if __name__ == '__main__':

	# log into database
	database = pymysql.connect(**json.load(open('database.json')))
    cursor = database.cursor()

    # create tables
    #cursor.execute('create table games (league text, home_team text, away_team text, date date);')
#, home_win float, away_win float, home_proj_score float, away_proj_score float, home_spread, away_spread, home_total, away_total
    # finished
	database.close()