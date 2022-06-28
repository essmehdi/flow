import logging
import os
import json
import sqlite3
from gi.repository import GLib

class StatusManager:

    DB_PATH = os.path.join(GLib.get_home_dir(), '.flow/data.db')

    @staticmethod
    def create_tables():
        con = sqlite3.connect(StatusManager.DB_PATH)
        cur = con.cursor()
        cur.execute('''CREATE TABLE downloads (
                id INTEGER CONSTRAINT pk_id PRIMARY KEY,
                filename TEXT,
                url TEXT,
                date_initiated INTEGER,
                date_started INTEGER,
                date_finished INTEGER,
                tmp TEXT,
                custom_headers TEXT,
                status TEXT,
                category TEXT,
                output_directory TEXT,
                size INTEGER,
                resumable INTEGER,
                info_parsed INTEGER
            )''')   
        con.commit()
        con.close()

    @staticmethod
    def get_connection():
        logging.info(f"Connecting to SQLite database: {StatusManager.DB_PATH}")
        if not os.path.exists(StatusManager.DB_PATH):
            StatusManager.create_tables()
        con = sqlite3.connect(StatusManager.DB_PATH)
        con.row_factory = sqlite3.Row
        return con

    @staticmethod
    def get_downloads(finished):
        with StatusManager.get_connection() as con:
            cur = con.cursor()
            cur.execute(f"SELECT * FROM downloads WHERE status {'=' if finished else '<>'} 'done' ORDER BY date_finished DESC",)
            results = cur.fetchall()
            cur.close()
            return results
        con.close()

    @staticmethod
    def update_property(id, property, value):
        with StatusManager.get_connection() as con:
            query = f"UPDATE downloads SET { property } = ? WHERE id = ?"
            cur = con.cursor()
            cur.execute(query, (value, id))
            cur.close()
        con.close()

    def register_download(**kwargs):
        kwargs['date_initiated'] = GLib.DateTime.new_now_local().to_unix()
        with StatusManager.get_connection() as con:    
            columns = ','.join(kwargs.keys())
            cur = con.cursor()
            cur.execute(f"INSERT INTO downloads ({ columns }) VALUES (?{ ',?' * (len(kwargs.values())-1) })", tuple(kwargs.values()))
            kwargs['id'] = cur.lastrowid
            return kwargs
        con.close()

    def remove_download(id, delete_file=False):
        with StatusManager.get_connection() as con:
            cur = con.cursor()
            cur.execute('SELECT filename, output_directory, tmp, size, status FROM downloads WHERE id = ?', (id,))
            result = cur.fetchone()
            cur.close()
            if result:
                path = os.path.join(result['output_directory'], result['filename'])
                if delete_file and result['status'] == 'done':
                    path = os.path.join(result['output_directory'], result['filename'])
                    # A naive precaution to be sure it's the downloaded file
                    if os.path.exists(path) and os.path.getsize(path) == result['size']:
                        logging.info("File found. Deleting...")
                        os.remove(path)
                    else:
                        logging.info("File not found")
                if result['status'] != 'done':
                    tmp = result['tmp']
                    if tmp and os.path.exists(tmp):
                        os.remove(tmp)

                con.execute("DELETE FROM downloads WHERE id = ?", (id,))
            else:
                logging.error(f"Attempted to delete a non-existant download (ID: {id})")
        con.close()
        
    @staticmethod
    def download_finished(id):
        with StatusManager.get_connection() as con:
            con.execute("UPDATE downloads SET status = 'done' WHERE id = ?", (id,))
        con.close()


if __name__ == '__main__':
    logging.info(StatusManagerDB.get_downloads(False))