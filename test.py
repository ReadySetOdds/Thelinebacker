import pymysql.cursors

# Connect to the database
connection = pymysql.connect(host='db-mysql-nyc1-01577-do-user-6792095-0.a.db.ondigitalocean.com',
                             user='doadmin',
                             password='ik4z3ww84adqhcoa',
                             port=25060,
                             database='defaultdb')

print(connection)