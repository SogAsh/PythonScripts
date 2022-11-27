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

def setKktAndPos(session, cashboxId, kkt: list, pos: list):
    settings = getCashoxSettingsJson(session, cashboxId)
    legalEntities = getLE(settings, len(kkt) == 2)
    le = []
    for i in range (len(legalEntities)):
        le.append(legalEntities[i]["legalEntityId"])

    settings["settings"]["backendSettings"]["legalEntities"] = legalEntities
    backendSettings = {"settings" : settings["settings"]["backendSettings"]}
    backendSettings["previousVersion"] = settings["versions"]["backendVersion"]

    settings["settings"]["appSettings"]["hardwareSettings"]["kkmSettings"] = getKkm(kkt, le)
    settings["settings"]["appSettings"]["hardwareSettings"]["cardTerminalSettings"] = getTerminal(pos, le)
    appSettings = {"settings" : settings["settings"]["appSettings"]}
    appSettings["previousVersion"] = settings["versions"]["appVersion"]

    postCashboxSettings(session, cashboxId, backendSettings, True)
    postCashboxSettings(session, cashboxId, appSettings, False)
    return le


def getLE(settings, twoLE : bool):
    legalEntities = list(settings["settings"]["backendSettings"]["legalEntities"])
    if (twoLE and len(legalEntities) == 1):
        legalEntities.append({"legalEntityId": "d4ab40fe-cf40-4a5f-8636-32a1efbd66af", "inn": "992570272700","kpp": "", "name": "ИП"})
    if (not twoLE):
        legalEntities = [legalEntities[0]]
    legalEntities[0]["inn"] = "6699000000"
    if (len(legalEntities) == 2):
        legalEntities[1]["inn"] = "992570272700"
    return legalEntities

def getKkm(kkt: list, le: list):
    result = []
    for i in range(len(kkt)):
        result.append({"kkmProtocol": f"{kkt[i]}", "allowOfdTransportConfiguration": True, "legalEntityId": le[i]})
    return result

def getTerminal(pos: list, le: list):
    result = []
    for i in range(len(pos)):
        result.append({"cardTerminalProtocol": pos[i], "legalEntityId": le[i],"merchantId": None})
    return result


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