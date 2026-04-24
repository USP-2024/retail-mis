import sqlite3
import os
from config import DATABASE_PATH
from utils.logger import log

class DBManager:
    def __init__(self):
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)

    def save(self, df, table):
        try:
            df.to_sql(table, self.conn, if_exists='replace', index=False)
            log(f"Saved {len(df)} rows to table '{table}'")
        except Exception as e:
            log(f"DB save error for table '{table}': {e}", "error")

    def query(self, sql):
        try:
            import pandas as pd
            return pd.read_sql_query(sql, self.conn)
        except Exception as e:
            log(f"DB query error: {e}", "error")
            return None

    def close(self):
        self.conn.close()