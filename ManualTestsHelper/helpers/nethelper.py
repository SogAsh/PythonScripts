import requests
import json
import pyperclip
import random

API_URL = "https://market.testkontur.ru:443/cashboxApi/backend/v1/cashbox/"

def startSession():
    session = requests.session()
    session.auth = ('admin', 'psw')
    session.headers['Accept'] = "application/json"
    return session

def genToken(session: requests.Session, cashboxId):
    session.headers['Content-Type'] = "application/json"
    url = API_URL + f"{cashboxId}/resetPassword"
    for i in range(10):
        token = str(random.randrange(11111111, 99999999))
        pyperclip.copy(f"{token}")
        data = json.dumps({"Token" : token})
        result = session.post(url, data = data)
        if result.ok: break

def getCashoxSettingsJson (session: requests.Session, cashboxId):
    response = session.get(API_URL + f'{cashboxId}/settings')
    return json.loads(response.content)

def postCashboxSettings(session: requests.Session, cashboxId, settings):
    session.headers['Content-Type'] = "application/json"
    session.post(API_URL + f"{cashboxId}/settings/backend", data = json.dumps(settings))

def flipBoolSettings(settings, settingsName, settingsType = "backendSettings"):
    settings["settings"][settingsType][settingsName] = not settings["settings"][settingsType][settingsName]
    result = {}
    result["settings"] = settings["settings"][settingsType]
    result["previousVersion"] = settings["versions"]["backendVersion"]
    return result

def getSavedCashboxName(session: requests.Session, cashboxId):
    backendSettings = getCashoxSettingsJson(session, cashboxId)['settings']['backendSettings']
    return f"shop: {backendSettings['shopName']}, cashbox: {backendSettings['cashboxName']}"