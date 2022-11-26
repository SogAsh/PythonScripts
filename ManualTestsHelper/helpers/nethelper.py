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
    legalEntities = getLE(settings)
    le1 = legalEntities[0]["legalEntityId"]
    le2 = legalEntities[1]["legalEntityId"]

    settings["settings"]["backendSettings"]["legalEntities"] = legalEntities
    backendSettings = {"settings" : settings["settings"]["backendSettings"]}
    backendSettings["previousVersion"] = settings["versions"]["backendVersion"]

    settings["settings"]["appSettings"]["hardwareSettings"]["kkmSettings"] = getKkm([kkt1,kkt2], [le1, le2])
    settings["settings"]["appSettings"]["hardwareSettings"]["cardTerminalSettings"] = get2terminal()
    appSettings = {"settings" : settings["settings"]["appSettings"]}
    appSettings["previousVersion"] = settings["versions"]["appVersion"]

    postCashboxSettings(session, cashboxId, backendSettings, True)
    postCashboxSettings(session, cashboxId, appSettings, False)

def getLE(settings, twoLE = True):
    legalEntities = list(settings["settings"]["backendSettings"]["legalEntities"])
    if (twoLE and len(legalEntities) == 1):
        legalEntities.append({"legalEntityId": "d4ab40fe-cf40-4a5f-8636-32a1efbd66af", "inn": "992570272700","kpp": "", "name": "ИП"})
    legalEntities[0]["inn"] = "6699000000"
    if (len(legalEntities) == 2):
        legalEntities[1]["inn"] = "992570272700"
    return legalEntities

def getKkm(kkt: list, le: list):
    result = []
    for i in range(len(kkt)):
        result.append({"kkmProtocol": f"{kkt[i]}", "allowOfdTransportConfiguration": True, "legalEntityId": le[i]})
    return result

# def get2terminal(kkt: list, le: list):
#     result = []
#     for i in range(len(kkt)):
#         result.append({"kkmProtocol": f"{kkt[i]}", "allowOfdTransportConfiguration": True, "legalEntityId": le[i]})
#     return result

def get2terminal():
    terminal1 = {"cardTerminalProtocol": "none", "legalEntityId": "e739e821-7b51-4a13-9c38-c8073c2ec644","merchantId": None}
    terminal2 = {"cardTerminalProtocol": "none", "legalEntityId": "d4ab40fe-cf40-4a5f-8636-32a1efbd66af", "merchantId": None}
    return [terminal1, terminal2]





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