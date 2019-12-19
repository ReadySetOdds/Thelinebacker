
# import dependencies
import pymysql, json

# main
if __name__ == '__main__':

	# log into database
    database = pymysql.connect(**json.load(open('database.json')))
    cursor = database.cursor()

    # databases
    for name in ('odds',):
        cursor.execute('SELECT * FROM {};'.format(name))
        database.commit()
        for item in cursor.fetchall():
            print(item)

    # finish
    database.close()