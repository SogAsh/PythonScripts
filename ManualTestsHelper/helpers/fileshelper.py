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

ALPHABET80 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!\"%&'*+-./_,:;=<>?"

def gen_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def encode_price_for_mark(price): 
    symbolNumbers = [] 
    while(True): 
        symbolNumbers.append(price % 80 ) 
        price = price // 80  
        if (price == 0):  
            break 
    leadingZeros = 4 - len(symbolNumbers)
    for _ in range(leadingZeros):
        symbolNumbers.append(0)
    res = "" 
    for number in range(len(symbolNumbers) - 1, -1, -1): 
        res += ALPHABET80[symbolNumbers[number]] 
    return res

def get_mark_from_file(productType):
    path = os.path.join(os.path.dirname(__file__), "marks", productType + ".txt")
    with open(path, "r") as file:
        lines = file.readlines()
        return lines[random.randrange(len(lines))].strip()

def paste_mark_in_scanner_mode(productType, bufferMode: bool, quietMode: bool):
    mark = ""
    if quietMode:
        mark = get_from_local_json("lastMark")
    elif bufferMode:
        mark = pyperclip.paste()
    else:  
        barcode = ""
        try:
            barcode = get_from_local_json("barcode") 
        except: 
            barcode = "2100000000463"
        if productType == "Tabak": 
            print("Какой нужен МРЦ в копейках?") 
            price = int(input().strip()) 
            mark = "0" + barcode + "-UWzSA8" + encode_price_for_mark(price) + gen_random_string(5)
        elif productType == "Cis":
            mark = "010" + barcode + "21" + gen_random_string(13) + "93" +  gen_random_string(13)
        elif productType == "Milk":
            mark = "010" + barcode + "21" + gen_random_string(8) + "93" + gen_random_string(4)
        else:  
            mark = get_mark_from_file(productType) 
    cache_in_local_json("lastMark", mark)
    keyboard.press_and_release("alt + tab")
    time.sleep(1)
    for i in range(len(mark)):
        keyboard.write(mark[i])
        time.sleep(0.01)

def set_db_connection():
    return sqlite3.connect(os.path.join(find_cashbox_path(), "db", "db.db"))

def update_products_with_pattern(cur : sqlite3.Cursor, products, legalEntityId, productNamePattern="", printName = False): 
    noProductsSet = True 
    for row in products: 
        product = json.loads(row[2]) 
        if (productNamePattern in product["name"]): 
            product["legalEntityId"] = legalEntityId 
            try:
                cur.execute(f"UPDATE Product SET Content = '{json.dumps(product)}' WHERE Id == {row[0]}") 
                if (printName):
                    print("Название товара для второго ЮЛ: " + product["name"])
                noProductsSet = False 
            except:
                pass
    return noProductsSet

def set_legalentityid_in_products(le, finalQuery = False):
    con = set_db_connection()
    cur = con.cursor()
    cur.execute("SELECT * FROM Product")
    products = cur.fetchall()
    if len(products) != 0:
        update_products_with_pattern(cur, products, le[0], "")
        if (len(le) > 1):
            noProductsFor2UL = update_products_with_pattern(cur, products, le[1], "_2ЮЛ", True)
            if (noProductsFor2UL):
                update_products_with_pattern(cur, [products[0]], le[1], "", True)
        con.commit()
    if finalQuery:
        con.close()

def get_last_receipt(con : sqlite3.Connection, finalQuery = False):
    cur = con.cursor()
    cur.execute("SELECT * FROM Receipt")
    result = cur.fetchall()[-1] #id, shiftid, number, content
    if finalQuery:
        con.close()
    return result

def update_receipt_content(con : sqlite3.Connection, content, id, finalQuery = False):
    query = f"UPDATE Receipt SET Content = '{content}' WHERE Id == '{id}'"
    cur = con.cursor()
    cur.execute(query)
    con.commit()
    if finalQuery: 
        con.close()

def get_cashbox_id():
    con = set_db_connection()
    cur = con.cursor()
    cur.execute("select * FROM CashboxState")
    cashboxId = cur.fetchall()[0][1]
    con.close()
    if cashboxId == None: 
        return get_from_local_json("cashboxId")
    cache_in_local_json("cashboxId", cashboxId)
    return cashboxId

def get_last_shift_from_db(con : sqlite3.Connection, finalQuery = False):
    cur = con.cursor()
    cur.execute("SELECT Content FROM shift WHERE Number == (SELECT Max(Number) FROM shift)")
    shift = cur.fetchone()[0] 
    if (finalQuery):
        con.close()
    return shift

def edit_shift_in_db(con : sqlite3.Connection, content : str, finalQuery = False):
    cur = con.cursor()
    query = f"UPDATE shift SET Content = '{content}' WHERE Number == (SELECT MAX(Number) FROM shift)"
    cur.execute(query)
    con.commit()
    if (finalQuery):
        con.close()

def close_sqlite(): 
    try:
        subprocess.call(["taskkill", "/f", "/im", "DB Browser for SQLite.exe"])
    except:
        pass

def delete_folder(filePath):
    close_sqlite()
    try:
        shutil.rmtree(filePath)
    except:
        print(f"Не удалось удалить папку с адресом:\n{filePath}")

def find_cashbox_path():
    for path in get_programfiles_paths():
        dir = find_child_dir_path(path, "SKBKontur")
        if dir != "":
            cashboxPath = os.path.join(path, "SKBKontur", "Cashbox")   
    return cashboxPath

def find_config_path():
    cashbox = find_cashbox_path()
    bin = os.path.join(cashbox, "bin")
    for root, dirs, files in os.walk(bin):
        configPath = os.path.join(root, dirs[0], "cashboxService.config.json")
        break
    assert configPath != "", "Can't find config path"
    cache_in_local_json("configPath", configPath)
    return configPath

def set_staging(stagingNumber):
    change_cashbox_service_state(True)
    configPath = find_config_path()
    change_staging_in_config(stagingNumber, configPath)
    change_cashbox_service_state(False)

def get_backend_url_from_config(configPath):
    with open(configPath, "r") as file:
        rawJson = file.read()
        return json.loads(rawJson)["settings"][0]["cashboxBackendUrl"]

def change_staging_in_config(stagingNumber, configPath):
    with open(configPath, "r+") as file:
        rawJson = file.read()
        data = json.loads(rawJson)
        if stagingNumber == 2:
            data["settings"][0]["loyaltyCashboxClientUrl"] = "https://market-dev.testkontur.ru/loyaltyCashboxApi"
            data["settings"][0]["cashboxBackendUrl"] = "https://market-dev.testkontur.ru"
        elif stagingNumber == 9:
            data["settings"][0]["loyaltyCashboxClientUrl"] = "https://market.kontur.ru/loyaltyCashboxApi"
            data["settings"][0]["cashboxBackendUrl"] = "https://market.kontur.ru"
        else: 
            data["settings"][0]["loyaltyCashboxClientUrl"] = "https://market.testkontur.ru/loyaltyCashboxApi"
            data["settings"][0]["cashboxBackendUrl"] = "https://market.testkontur.ru"

        newJson = json.dumps(data, indent=4)
        file.seek(0)
        file.write(newJson)
        file.truncate()   

def change_cashbox_service_state(shouldStop):
    try:
        subprocess.call(['sc', f'{"stop" if shouldStop else "start"}', 'SKBKontur.Cashbox'])
        time.sleep(1 if shouldStop else 4)
        return True
    except:
        return False

def find_child_dir_path(path, dir):
    for root, dirs, files in os.walk(path):
        if (dir in dirs):
            return os.path.join(root, dir)
        break 
    return "" 

def get_programfiles_paths():
    paths = []
    for diskDrive in get_from_local_json("diskDrives"):
        paths.append(os.path.join(diskDrive, "Program Files"))
        paths.append(os.path.join(diskDrive, "Program Files (x86)"))
    return paths

def cache_in_local_json(key, value):
    path = os.path.join(os.path.dirname(__file__), "data.json")
    with open(path, "r+") as file:
        rawJson = file.read()
        data = json.loads(rawJson)
        data[key] = value
        newJson = json.dumps(data, indent=4)
        file.seek(0)
        file.write(newJson)
        file.truncate()

def get_from_local_json(key):
    path = os.path.join(os.path.dirname(__file__), "data.json")
    with open(path, "r") as file:
        rawJson = file.read()
        data = json.loads(rawJson)
        assert key in data, f"Key {key} not in {path}"
        return data[key]