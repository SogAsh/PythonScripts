import requests
import json
import pyperclip
import random
import time

API_URL = "https://market.testkontur.ru:443/cashboxApi/backend/v1/cashbox/"
V2_API_URL = "https://market.testkontur.ru:443/cashboxApi/backend/v2/cashbox/"

def startSession():
    session = requests.session()
    session.auth = ('admin', 'psw')
    session.headers['Accept'] = "application/json"
    return session

def genToken(session: requests.Session, cashboxId, attemptsNumber = 5):
    session.headers['Content-Type'] = "application/json"
    url = API_URL + f"{cashboxId}/resetPassword"
    for i in range(attemptsNumber):
        token = str(random.randrange(11111111, 99999999))
        data = json.dumps({"Token" : token})
        result = session.post(url, data = data)
        print(f"Результат запроса {cashboxId}/resetPassword: {result}")
        if result.ok: 
            pyperclip.copy(f"{token}")
            break

def prepSettingsFor2UL(session, cashboxId, kkt1, kkt2):
    settings = getCashoxSettingsJson(session, cashboxId)

    backendSettings = {}
    backendSettings["settings"] = settings["settings"]["backendSettings"]
    backendSettings["previousVersion"] = settings["versions"]["backendVersion"]
    backendSettings["settings"]["legalEntities"] = get2LE()["legalEntities"]

    appSettings = {}
    appSettings["settings"] = settings["settings"]["appSettings"]
    appSettings["previousVersion"] = settings["versions"]["appVersion"]
    appSettings["settings"]["hardwareSettings"]["kkmSettings"] = get2Kkm(kkt1,kkt2)["kkmSettings"]
    appSettings["settings"]["hardwareSettings"]["cardTerminalSettings"] = get2terminal()["cardTerminalSettings"]

    postCashboxSettings(session, cashboxId, backendSettings, True)
    postCashboxSettings(session, cashboxId, appSettings, False)


def get2Kkm(kkt1, kkt2):
    kkm1 = {"kkmProtocol": f"{kkt1}", "allowOfdTransportConfiguration": True, "legalEntityId": "e739e821-7b51-4a13-9c38-c8073c2ec644"}
    kkm2 = {"kkmProtocol": f"{kkt2}","allowOfdTransportConfiguration": True, "legalEntityId": "d4ab40fe-cf40-4a5f-8636-32a1efbd66af"}
    return {"kkmSettings" : [kkm1, kkm2]}

def get2terminal():
    terminal1 = {"cardTerminalProtocol": "none", "legalEntityId": "e739e821-7b51-4a13-9c38-c8073c2ec644","merchantId": None}
    terminal2 = {"cardTerminalProtocol": "none", "legalEntityId": "d4ab40fe-cf40-4a5f-8636-32a1efbd66af", "merchantId": None}
    return {"cardTerminalSettings" : [terminal1, terminal2]}


def get2LE():
    LE1 = {"legalEntityId": "e739e821-7b51-4a13-9c38-c8073c2ec644", "inn": "6699000000", "kpp": "", "name": "Юрлицо"}
    LE2 = {"legalEntityId": "d4ab40fe-cf40-4a5f-8636-32a1efbd66af", "inn": "992570272700","kpp": "", "name": "ИП"}
    return {"legalEntities" : [LE1, LE2]}




def getCashoxSettingsJson (session: requests.Session, cashboxId):
    response = session.get(V2_API_URL + f'{cashboxId}/settings')
    return json.loads(response.content)

def postCashboxSettings(session: requests.Session, cashboxId, settings, backend = True):
    settingsType = "backend" if backend else "app"
    session.headers['Content-Type'] = "application/json"
    result = session.post(V2_API_URL + f"{cashboxId}/settings/" + f"{settingsType}", data = json.dumps(settings))
    print(result)

def flipBoolSettings(settings, settingsName, settingsType = "backendSettings"):
    settings["settings"][settingsType][settingsName] = not settings["settings"][settingsType][settingsName]
    result = {}
    result["settings"] = settings["settings"][settingsType]
    result["previousVersion"] = settings["versions"]["backendVersion"]
    return result

def getSavedCashboxName(session: requests.Session, cashboxId):
    backendSettings = getCashoxSettingsJson(session, cashboxId)['settings']['backendSettings']
    return f"shop: {backendSettings['shopName']}, cashbox: {backendSettings['cashboxName']}"