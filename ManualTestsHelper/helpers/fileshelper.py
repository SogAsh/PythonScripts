import os
import shutil
import json
import subprocess 
import sqlite3
import time
import keyboard
import pyperclip
import random
import string

class Mark():


    ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!\"%&'*+-./_,:;=<>?"
    
    def encode_price_for_mark(price): 
        positions = [] 
        while(True): 
            positions.append(price % 80 ) 
            price = price // 80  
            if (price == 0):  
                break 
        leading_zeros = 4 - len(positions)
        for _ in range(leading_zeros):
            positions.append(0)
        res = "" 
        for number in range(len(positions) - 1, -1, -1): 
            res += Mark.ALPHABET[positions[number]] 
        return res

    def get_mark_from_file(product_type):
        path = os.path.join(os.path.dirname(__file__), "marks", product_type + ".txt")
        with open(path, "r") as file:
            lines = file.readlines()
            return lines[random.randrange(len(lines))].strip()

    def paste_mark_in_scanner_mode(product_type, buffer_mode: bool, quiet_mode: bool):
        mark = ""
        if quiet_mode:
            mark = OS.get_from_local_json("lastMark")
        elif buffer_mode:
            mark = pyperclip.paste()
        else:  
            barcode = ""
            try:
                barcode = OS.get_from_local_json("barcode") 
            except: 
                barcode = "2100000000463"
            if product_type == "Tabak": 
                print("Какой нужен МРЦ в копейках?") 
                price = int(input().strip()) 
                mark = "0" + barcode + "-UWzSA8" + Mark.encode_price_for_mark(price) + OS.gen_random_string(5)
            elif product_type == "Cis":
                mark = "010" + barcode + "21" + OS.gen_random_string(13) + "93" +  OS.gen_random_string(13)
            elif product_type == "Milk":
                mark = "010" + barcode + "21" + OS.gen_random_string(8) + "93" + OS.gen_random_string(4)
            else:  
                mark = Mark.get_mark_from_file(product_type) 
        OS.cache_in_local_json("lastMark", mark)
        if not quiet_mode:
            keyboard.press_and_release("alt + tab")
        time.sleep(1)
        for i in range(len(mark)):
            keyboard.write(mark[i])
            time.sleep(0.01)

class DB():


    def __init__(self):
        self.session = self.set_db_connection()
        self.con = self.set_db_connection()
        self.cur = self.con.cursor()

    def set_db_connection(self):
        return sqlite3.connect(os.path.join(OS.find_cashbox_path(), "db", "db.db"))

    def update_products_with_pattern(self, products, legalEntityId, pattern="", should_print_name = False): 
        no_products_set = True 
        for row in products: 
            product = json.loads(row[2]) 
            if (pattern in product["name"]): 
                product["legalEntityId"] = legalEntityId 
                try:
                    self.cur.execute(f"UPDATE Product SET Content = '{json.dumps(product)}' WHERE Id == {row[0]}") 
                    if (should_print_name):
                        print("Название товара для второго ЮЛ: " + product["name"])
                    no_products_set = False 
                except:
                    pass
        return no_products_set

    def set_legalentityid_in_products(self, le, final_query = False):
        self.cur.execute("SELECT * FROM Product")
        products = self.cur.fetchall()
        if len(products) != 0:
            self.update_products_with_pattern(products, le[0], "")
            if (len(le) > 1):
                no_products_set = self.update_products_with_pattern(products, le[1], "_2ЮЛ", True)
                if (no_products_set):
                    self.update_products_with_pattern([products[0]], le[1], "", True)
            self.con.commit()
        if final_query:
            self.con.close()

    def get_last_receipt(self, final_query = False):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM Receipt")
        result = cur.fetchall()[-1] #id, shiftid, number, content
        if final_query:
            self.con.close()
        return result

    def update_receipt_content(self, content, id, final_query = False):
        query = f"UPDATE Receipt SET Content = '{content}' WHERE Id == '{id}'"
        self.cur.execute(query)
        self.con.commit()
        if final_query: 
            self.con.close()

    def get_cashbox_id(self, final_query = False):
        self.cur.execute("select * FROM CashboxState")
        cashbox_id = self.cur.fetchall()[0][1]
        if cashbox_id == None: 
            return OS.get_from_local_json("cashboxId")
        OS.cache_in_local_json("cashboxId", cashbox_id)
        if (final_query):
            self.con.close()
        return cashbox_id

    def get_last_shift_from_db(self, final_query = False):
        cur = self.con.cursor()
        cur.execute("SELECT Content FROM shift WHERE Number == (SELECT Max(Number) FROM shift)")
        shift = cur.fetchone()[0] 
        if (final_query):
            self.con.close()
        return shift

    def edit_shift_in_db(self, content : str, final_query = False):
        cur = self.con.cursor()
        query = f"UPDATE shift SET Content = '{content}' WHERE Number == (SELECT MAX(Number) FROM shift)"
        cur.execute(query)
        self.con.commit()
        if (final_query):
            self.con.close()
    
    def __del__(self):
        try:
            self.con.close()
        except:
            print("Объект БД уничтожен")

class OS():


    @staticmethod
    def close_sqlite(): 
        try:
            subprocess.call(["taskkill", "/f", "/im", "DB Browser for SQLite.exe"])
        except:
            pass

    @staticmethod
    def delete_folder(file_path):
        OS.close_sqlite()
        try:
            shutil.rmtree(file_path)
        except:
            print(f"Не удалось удалить папку с адресом:\n{file_path}")

    @staticmethod
    def find_cashbox_path():
        for path in OS.get_programfiles_paths():
            dir = OS.find_child_dir_path(path, "SKBKontur")
            if dir != "":
                cashbox_path = os.path.join(path, "SKBKontur", "Cashbox")   
        return cashbox_path

    @staticmethod
    def find_config_path():
        cashbox = OS.find_cashbox_path()
        bin = os.path.join(cashbox, "bin")
        for root, dirs, files in os.walk(bin):
            config_path = os.path.join(root, dirs[0], "cashboxService.config.json")
            break
        assert config_path != "", "Can't find config path"
        OS.cache_in_local_json("configPath", config_path)
        return config_path

    @staticmethod
    def set_staging(stage):
        OS.change_cashbox_service_state(True)
        OS.change_staging_in_config(stage, OS.find_config_path())
        OS.change_cashbox_service_state(False)

    @staticmethod
    def get_backend_url_from_config(config_path):
        with open(config_path, "r") as file:
            raw = file.read()
            return json.loads(raw)["settings"][0]["cashboxBackendUrl"]

    @staticmethod
    def change_staging_in_config(stage, config_path):
        with open(config_path, "r+") as file:
            raw = file.read()
            data = json.loads(raw)
            if stage == 2:
                data["settings"][0]["loyaltyCashboxClientUrl"] = "https://market-dev.testkontur.ru/loyaltyCashboxApi"
                data["settings"][0]["cashboxBackendUrl"] = "https://market-dev.testkontur.ru"
            elif stage == 9:
                data["settings"][0]["loyaltyCashboxClientUrl"] = "https://market.kontur.ru/loyaltyCashboxApi"
                data["settings"][0]["cashboxBackendUrl"] = "https://market.kontur.ru"
            else: 
                data["settings"][0]["loyaltyCashboxClientUrl"] = "https://market.testkontur.ru/loyaltyCashboxApi"
                data["settings"][0]["cashboxBackendUrl"] = "https://market.testkontur.ru"

            newJson = json.dumps(data, indent=4)
            file.seek(0)
            file.write(newJson)
            file.truncate()   

    @staticmethod
    def change_cashbox_service_state(should_stop):
        try:
            subprocess.call(['sc', f'{"stop" if should_stop else "start"}', 'SKBKontur.Cashbox'])
            time.sleep(1 if should_stop else 4)
            return True
        except:
            return False

    @staticmethod
    def find_child_dir_path(path, dir):
        for root, dirs, files in os.walk(path):
            if (dir in dirs):
                return os.path.join(root, dir)
            break 
        return "" 

    @staticmethod
    def get_programfiles_paths():
        paths = []
        for disk_drive in OS.get_from_local_json("diskDrives"):
            paths.append(os.path.join(disk_drive, "Program Files"))
            paths.append(os.path.join(disk_drive, "Program Files (x86)"))
        return paths

    @staticmethod
    def cache_in_local_json(key, value):
        path = os.path.join(os.path.dirname(__file__), "data.json")
        with open(path, "r+") as file:
            raw = file.read()
            data = json.loads(raw)
            data[key] = value
            newJson = json.dumps(data, indent=4)
            file.seek(0)
            file.write(newJson)
            file.truncate()

    @staticmethod
    def get_from_local_json(key):
        path = os.path.join(os.path.dirname(__file__), "data.json")
        with open(path, "r") as file:
            rawJson = file.read()
            data = json.loads(rawJson)
            assert key in data, f"Key {key} not in {path}"
            return data[key]
    
    @staticmethod
    def gen_random_string(length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))