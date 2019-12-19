
# import dependencies
import pymysql, json

# main
if __name__ == '__main__':

	# log into database
    database = pymysql.connect(**json.load(open('database.json')))
    cursor = database.cursor()

    # create tables
    for table_name, values in (
        ('odds', 'league TEXT, home_team TEXT, away_team TEXT, date TIMESTAMP, odds_group TEXT, home_odds_1 FLOAT, home_odds_2 FLOAT, away_odds_1 FLOAT, away_odds_2 FLOAT, price_total FLOAT, odds_over FLOAT, odds_under FLOAT'),
    ):

        # delete existing
        cursor.execute('DROP TABLE IF EXISTS {};'.format(table_name))
        database.commit()

        # create table
        cursor.execute('create table {} ({});'.format(table_name, values))
        database.commit()

    # create tables
    #cursor.execute('create table games (league text, home_team text, away_team text, date date);')
#, home_win float, away_win float, home_proj_score float, away_proj_score float, home_spread, away_spread, home_total, away_total
    # finished
    database.close()