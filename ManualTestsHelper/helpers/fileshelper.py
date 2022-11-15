import os
import shutil
import json
import subprocess 
import sqlite3
import time
import uuid
import ctypes

def printMsg(title, text, style = 0):
    ctypes.windll.user32.MessageBoxW(0, text, title, style)

def setDbConnection():
    # closeSQLite()
    return sqlite3.connect(os.path.join(findCashboxPath(), "db", "db.db"))

def getLastReceipt(con : sqlite3.Connection, finalQuery = False):
    cur = con.cursor()
    cur.execute("select * from Receipt")
    result = cur.fetchall()[-1] #id, shiftid, number, content
    if finalQuery:
        con.close()
    return result

def updateReceiptContent(con : sqlite3.Connection, content, id, finalQuery = False):
    query = f"UPDATE Receipt SET Content = '{content}' WHERE Id == '{id}'"
    cur = con.cursor()
    cur.execute(query)
    con.commit()
    if finalQuery: 
        con.close()

def getCashboxId():
    con = setDbConnection()
    cur = con.cursor()
    cur.execute("select * FROM CashboxState")
    cashboxId = cur.fetchall()[0][1]
    con.close()
    if cashboxId == None: 
        return readJsonValue("cashboxId")
    writeJsonValue("cashboxId", cashboxId)
    return cashboxId

def getLastShiftFromDb(con : sqlite3.Connection, finalQuery = False):
    cur = con.cursor()
    cur.execute("SELECT Content FROM shift WHERE Number == (SELECT Max(Number) FROM shift)")
    shift = cur.fetchone()[0] 
    if (finalQuery):
        con.close()
    return shift

def editShiftInDB(con : sqlite3.Connection, content : str, finalQuery = False):
    cur = con.cursor()
    query = f"UPDATE shift SET Content = '{content}' WHERE Number == (SELECT MAX(Number) FROM shift)"
    cur.execute(query)
    con.commit()
    if (finalQuery):
        con.close()

def closeSQLite(): 
    try:
        subprocess.call(["taskkill", "/f", "/im", "DB Browser for SQLite.exe"])
    except:
        pass

def deleteFolder(filePath):
    try:
        shutil.rmtree(filePath)
    except:
        pass

def findCashboxPath():
    for path in getProgramFilesPaths():
        dir = findChildDirPath(path, "SKBKontur")
        if dir != "":
            cashboxPath = os.path.join(path, "SKBKontur", "Cashbox")   
    return cashboxPath

def findConfigPath():
    cashbox = findCashboxPath()
    bin = os.path.join(cashbox, "bin")
    for root, dirs, files in os.walk(bin):
        configPath = os.path.join(root, dirs[0], "cashboxService.config.json")
        break
    assert configPath != "", "Can't find config path"
    writeJsonValue("configPath", configPath)
    return configPath

def setStaging(stagingNumber):
    configPath = findConfigPath()
    changeStagingInConfig(stagingNumber, configPath)

def changeStagingInConfig(stagingNumber, configPath):
    with open(configPath, "r+") as file:
        rawJson = file.read()
        data = json.loads(rawJson)
        if stagingNumber == 2:
            data["settings"][0]["loyaltyCashboxClientUrl"] = "https://market-dev.testkontur.ru/loyaltyCashboxApi"
            data["settings"][0]["cashboxBackendUrl"] = "https://market.testkontur.ru"
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

def changeCashboxServiceState(action):
    waitTime = 1 if action == "stop" else 4
    try:
        subprocess.call(['sc', f'{action}', 'SKBKontur.Cashbox'])
        time.sleep(waitTime)
    except:
        pass


def findChildDirPath(path, dir):
    for root, dirs, files in os.walk(path):
        if (dir in dirs):
            return os.path.join(root, dir)
        break 
    return "" 

def getProgramFilesPaths():
    paths = []
    for diskDrive in readJsonValue("diskDrives"):
        paths.append(os.path.join(diskDrive, "Program Files"))
        paths.append(os.path.join(diskDrive, "Program Files (x86)"))
    return paths

def writeJsonValue(key, value, path = os.path.join("helpers", "data.json")):
    with open(path, "r+") as file:
        rawJson = file.read()
        data = json.loads(rawJson)
        data[key] = value
        newJson = json.dumps(data, indent=4)
        file.seek(0)
        file.write(newJson)
        file.truncate()

def readJsonValue(key, path = os.path.join("helpers", "data.json")):
    with open(path, "r") as file:
        rawJson = file.read()
        data = json.loads(rawJson)
        assert key in data, f"Key {key} not in {path}"
        return data[key]