import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self, host='localhost', database='tayseer_db', user='root', password='Zakri@123'):
        self.config = {
            'host': host,
            'database': database,
            'user': user,
            'password': password
        }

    def get_connection(self):
        """إنشاء وإرجاع كائن الاتصال بقاعدة البيانات"""
        try:
            connection = mysql.connector.connect(**self.config)
            return connection
        except Error as e:
            print(f"[خطأ في الاتصال بقاعدة البيانات]: {e}")
            return None

    def check_health(self):
        """فحص حالة السيرفر"""
        try:
            conn = self.get_connection()
            if conn and conn.is_connected():
                version = conn.server_info
                conn.close()
                return True, version
            return False, "تعذر الاتصال"
        except Error as e:
            return False, str(e)