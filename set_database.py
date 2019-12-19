
# import dependencies
import pymysql, json

#BESTBETS rotation, league, date, match_details, play, line, odds, play_amount
#GAME league, home_team, away_team, date, home_win, away_win, home_proj_score, away_proj_score, spread_total, home_spread_1, home_spread_2, away_spread_1, away_spread_2, total, home_total, odds_under, away_total, odds_total
#ODDS league, home_team, away_team, date, odds_group, home_odds_1, home_odds_2, away_odds_1, away_odds_2, price_total, over, under

# main
if __name__ == '__main__':

	# log into database
    database = pymysql.connect(**json.load(open('database.json')))
    cursor = database.cursor()

    # create tables
    for table_name, values in (
        ('bestbets', 'rotation INTEGER, league TEXT, date TIMESTAMP, match_details TEXT, play TEXT, line FLOAT, odds INTEGER, play_amount INTEGER'),
        ('games', 'league TEXT, home_team TEXT, away_team TEXT, date TIMESTAMP, home_win FLOAT, away_win FLOAT, home_proj_score FLOAT, away_proj_score FLOAT, spread_total FLOAT, home_spread_1 FLOAT, home_spread_2 FLOAT, away_spread_1 FLOAT, away_spread_2 FLOAT, total FLOAT, home_total FLOAT, odds_under FLOAT, away_total FLOAT, odds_total FLOAT'),
        ('odds', 'league TEXT, home_team TEXT, away_team TEXT, date TIMESTAMP, odds_group TEXT, home_odds_1 FLOAT, home_odds_2 FLOAT, away_odds_1 FLOAT, away_odds_2 FLOAT, price_total FLOAT, odds_over FLOAT, odds_under FLOAT'),
    ):

        # delete existing
        cursor.execute('DROP TABLE IF EXISTS {};'.format(table_name))
        database.commit()

        # create table
        cursor.execute('create table {} ({});'.format(table_name, values))
        database.commit()

    # finished
    database.close()