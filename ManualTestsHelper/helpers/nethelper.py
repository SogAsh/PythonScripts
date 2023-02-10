import json
import random
import pyperclip
import requests

V1_URL_TAIL = ":443/cashboxApi/backend/v1/cashbox/"
V2_URL_TAIL = ":443/cashboxApi/backend/v2/cashbox/"

def start_session():
    session = requests.session()
    session.auth = ('admin', 'psw')
    session.headers['Accept'] = "application/json"
    return session

def gen_token_CS(session: requests.Session, cashboxId, backendUrl, attemptsNumber = 5):
    session.headers['Content-Type'] = "application/json"
    url = backendUrl + V1_URL_TAIL + f"{cashboxId}/resetPassword"
    for i in range(attemptsNumber):
        token = str(random.randrange(11111111, 99999999))
        data = json.dumps({"Token" : token})
        result = session.post(url, data = data)
        print(f"Результат запроса {cashboxId}/resetPassword: {result}")
        if result.ok: 
            pyperclip.copy(f"{token}")
            break

def change_hardware_settings(session, cashboxId, kkt: list, pos: list, backendUrl):
    settings = get_cashbox_settings_json(session, cashboxId, backendUrl)
    legalEntities = get_legalentity_ids(settings, len(kkt) == 2)
    le = []
    for i in range (len(legalEntities)):
        le.append(legalEntities[i]["legalEntityId"])

    settings["settings"]["backendSettings"]["legalEntities"] = legalEntities
    backendSettings = {"settings" : settings["settings"]["backendSettings"]}
    backendSettings["previousVersion"] = settings["versions"]["backendVersion"]

    settings["settings"]["appSettings"]["hardwareSettings"]["kkmSettings"] = get_kkm_settings(kkt, le)
    settings["settings"]["appSettings"]["hardwareSettings"]["cardTerminalSettings"] = get_terminal_settings(pos, le)
    appSettings = {"settings" : settings["settings"]["appSettings"]}
    appSettings["previousVersion"] = settings["versions"]["appVersion"]

    post_cashbox_settings(session, cashboxId, backendSettings, backendUrl, True)
    post_cashbox_settings(session, cashboxId, appSettings, backendUrl, False)
    return le

def get_legalentity_ids(settings, twoLE : bool):
    legalEntities = list(settings["settings"]["backendSettings"]["legalEntities"])
    if (twoLE and len(legalEntities) == 1):
        legalEntities.append({"legalEntityId": "d4ab40fe-cf40-4a5f-8636-32a1efbd66af", "inn": "992570272700","kpp": "", "name": "ИП"})
    if (not twoLE):
        legalEntities = [legalEntities[0]]
    legalEntities[0]["inn"] = "6699000000"
    if (len(legalEntities) == 2):
        legalEntities[1]["inn"] = "992570272700"
    return legalEntities

def get_kkm_settings(kkt: list, le: list):
    result = []
    for i in range(len(kkt)):
        result.append({"kkmProtocol": f"{kkt[i]}", "allowOfdTransportConfiguration": True, "legalEntityId": le[i]})
    return result

def get_terminal_settings(pos: list, le: list):
    result = []
    for i in range(len(pos)):
        result.append({"cardTerminalProtocol": pos[i], "legalEntityId": le[i],"merchantId": None})
    return result

def get_cashbox_settings_json (session: requests.Session, cashboxId, backendUrl):
    response = session.get(backendUrl + V2_URL_TAIL + f'{cashboxId}/settings')
    return json.loads(response.content)

def post_cashbox_settings(session: requests.Session, cashboxId, settings, backendUrl, backend = True):
    settingsType = "backend" if backend else "app"
    session.headers['Content-Type'] = "application/json"
    result = session.post(backendUrl + V2_URL_TAIL + f"{cashboxId}/settings/" + f"{settingsType}", data = json.dumps(settings))
    print(result)

def flip_settings_CS(settings, settingsName, settingsType = "backendSettings"):
    settings["settings"][settingsType][settingsName] = not settings["settings"][settingsType][settingsName]
    result = {}
    result["settings"] = settings["settings"][settingsType]
    result["previousVersion"] = settings["versions"]["backendVersion"]
    return result