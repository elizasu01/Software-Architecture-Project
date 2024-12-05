# db_utils.py
import pymysql

def get_db_connection():
    connection = pymysql.connect(
        host='localhost',
        user='wsu15',
        password='123456',
        database='appointments_db'
    )
    return connection
