import json
import os
import sys
import mysql.connector
from mysql.connector import Error


class Database:
    def __init__(self, host='localhost', database='', user='', password='', port=''):
        self.config = {
            'host': host,
            'port': int(port),
            'database': database,
            'user': user,
            'password': password,
            'charset': 'utf8mb4',
            'use_unicode': True,
        }

    @staticmethod
    def _get_base_dir() -> str:
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    @classmethod
    def from_config_file(cls, config_filename: str = 'clinic_config.json') -> 'Database':
        config_path = os.path.join(cls._get_base_dir(), config_filename)
        if not os.path.exists(config_path):
            return cls()

        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        db_cfg = data.get('db', data)
        return cls(
            host=db_cfg.get('host', 'localhost'),
            database=db_cfg.get('database', ''),
            user=db_cfg.get('user', 'root'),
            password=db_cfg.get('password', ''),
            port=db_cfg.get('port', 3306),
        )

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
