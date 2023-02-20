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
import requests
from console import fg, bg, fx
from enum import Enum

ERR = bg.lightred + fg.black

class Mode(Enum):
    NORMAL = 1, 
    CLIPBOARD = 2, 
    FILE = 3, 
    QUIET = 4

class Mark():
      
    
    ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!\"%&'*+-./_,:;=<>?"
    
    def paste_mark_in_scanner_mode(product_type, mode: Mode):
        mark = Mark.get_mark(product_type, mode)
        if mode != Mode.QUIET:
            keyboard.press_and_release("alt + tab")
        time.sleep(1)
        for i in range(len(mark)):
            keyboard.write(mark[i])
            time.sleep(0.01)

    def get_mark(product_type, mode:Mode):
        mark = ""
        if mode == Mode.QUIET:
            mark = OS.get_from_local_json("lastMark")
        elif mode == Mode.CLIPBOARD:
            mark = pyperclip.paste()
        else:
            barcode = OS.get_from_local_json("barcode") 
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
        return mark

    def get_mark_from_file(product_type):
        path = os.path.join(os.path.dirname(__file__), "marks", product_type + ".txt")
        with open(path, "r") as file:
            lines = file.readlines()
            return lines[random.randrange(len(lines))].strip()

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

class DB():


    def __init__(self):
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
    def change_cashbox_service_state(should_stop):
        subprocess.call(['sc', f'{"stop" if should_stop else "start"}', 'SKBKontur.Cashbox'])
        time.sleep(1 if should_stop else 4)


    @staticmethod
    def close_sqlite(): 
        try:
            subprocess.call(["taskkill", "/f", "/im", "DB Browser for SQLite.exe"])
        except:
            print("Не удалось закрыть SQLite")

    @staticmethod
    def delete_folder(file_path):
        OS.close_sqlite()
        try:
            shutil.rmtree(file_path)
        except:
            print(f"Не удалось удалить папку: {file_path}")

    @staticmethod
    def find_cashbox_path():
        program_files_dirs = []
        for disk_drive in OS.get_from_local_json("diskDrives"):
            program_files_dirs.append(os.path.join(disk_drive, "Program Files"))
            program_files_dirs.append(os.path.join(disk_drive, "Program Files (x86)"))
        for path in program_files_dirs:
            kontur_path = os.path.join(path, "SKBKontur")
            if os.path.exists(kontur_path):
                return os.path.join(kontur_path, "Cashbox")
        print(f"Не удалось найти папку Cashbox на жёстких дисках {OS.get_from_local_json('diskDrives')}")
        input()
        return ""

    @staticmethod
    def find_config_path():
        cashbox = OS.find_cashbox_path()
        bin = os.path.join(cashbox, "bin")
        config_path = ""
        for root, dirs, files in os.walk(bin):
            config_path = os.path.join(root, dirs[0], "cashboxService.config.json")
            break
        if config_path == "": 
            print("Не удалось найти файл конфига")
        OS.cache_in_local_json("configPath", config_path)
        return config_path

    @staticmethod
    def get_backend_url_from_config(config_path):
        with open(config_path, "r") as file:
            raw = file.read()
            return json.loads(raw)["settings"][0]["cashboxBackendUrl"]

    @staticmethod
    def change_staging_in_config(stage, config_path):
        OS.change_cashbox_service_state(True)
        with open(config_path, "r+") as file:
            data = json.loads(file.read())
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
        OS.change_cashbox_service_state(False)


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

class CS():


    def __init__(self):
        self.V1_URL_TAIL = ":443/cashboxApi/backend/v1/cashbox/"
        self.V2_URL_TAIL = ":443/cashboxApi/backend/v2/cashbox/"
        self.session = self.start_session()
        self.backend_url = OS.get_backend_url_from_config(OS.find_config_path())
        
    def start_session(self):
        session = requests.session()
        session.auth = ('admin', 'psw')
        session.headers['Accept'] = "application/json"
        return session

    def gen_token(self, cashbox_id, attempts = 5):
        self.session.headers['Content-Type'] = "application/json"
        url = self.backend_url + self.V1_URL_TAIL + f"{cashbox_id}/resetPassword"
        for i in range(attempts):
            token = str(random.randrange(11111111, 99999999))
            data = json.dumps({"Token" : token})
            result = self.session.post(url, data = data)
            print(f"Результат запроса {cashbox_id}/resetPassword: {result}")
            if result.ok: 
                pyperclip.copy(f"{token}")
                break

    def change_hardware_settings(self, cashbox_id, kkt: list, pos: list):
        settings = self.get_cashbox_settings_json(cashbox_id)
        legal_entities = self.get_legal_entity_ids(settings, len(kkt) == 2)
        le = []
        for i in range (len(legal_entities)):
            le.append(legal_entities[i]["legalEntityId"])

        settings["settings"]["backendSettings"]["legalEntities"] = legal_entities
        backend_settings = {"settings" : settings["settings"]["backendSettings"]}
        backend_settings["previousVersion"] = settings["versions"]["backendVersion"]

        settings["settings"]["appSettings"]["hardwareSettings"]["kkmSettings"] = self.get_kkm_settings(kkt, le)
        settings["settings"]["appSettings"]["hardwareSettings"]["cardTerminalSettings"] = self.get_terminal_settings(pos, le)
        app_settings = {"settings" : settings["settings"]["appSettings"]}
        app_settings["previousVersion"] = settings["versions"]["appVersion"]

        self.post_cashbox_settings(cashbox_id, backend_settings, True)
        self.post_cashbox_settings(cashbox_id, app_settings, False)
        return le

    def get_legal_entity_ids(self, settings, two_UL : bool):
        legal_entities = list(settings["settings"]["backendSettings"]["legalEntities"])
        if (two_UL and len(legal_entities) == 1):
            legal_entities.append({"legalEntityId": "d4ab40fe-cf40-4a5f-8636-32a1efbd66af", "inn": "992570272700","kpp": "", "name": "ИП"})
        if (not two_UL):
            legal_entities = [legal_entities[0]]
        legal_entities[0]["inn"] = "6699000000"
        if (len(legal_entities) == 2):
            legal_entities[1]["inn"] = "992570272700"
        return legal_entities

    def get_kkm_settings(self, kkt: list, le: list):
        result = []
        for i in range(len(kkt)):
            result.append({"kkmProtocol": f"{kkt[i]}", "allowOfdTransportConfiguration": True, "legalEntityId": le[i]})
        return result

    def get_terminal_settings(self, pos: list, le: list):
        result = []
        for i in range(len(pos)):
            result.append({"cardTerminalProtocol": pos[i], "legalEntityId": le[i],"merchantId": None})
        return result

    def get_cashbox_settings_json(self, cashboxId):
        response = self.session.get(self.backend_url + self.V2_URL_TAIL + f'{cashboxId}/settings')
        return json.loads(response.content)

    def post_cashbox_settings(self, cashboxId, settings, backend = True):
        settings_type = "backend" if backend else "app"
        self.session.headers['Content-Type'] = "application/json"
        result = self.session.post(self.backend_url + self.V2_URL_TAIL + f"{cashboxId}/settings/" + f"{settings_type}", data = json.dumps(settings))
        print(result)

    def flip_settings(self, settings, settings_name, settings_type = "backendSettings"):
        settings["settings"][settings_type][settings_name] = not settings["settings"][settings_type][settings_name]
        result = {}
        result["settings"] = settings["settings"][settings_type]
        result["previousVersion"] = settings["versions"]["backendVersion"]
        return result