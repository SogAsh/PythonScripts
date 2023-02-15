import json
import random
import pyperclip
import requests

class CS():


    def __init__(self):
        self.V1_URL_TAIL = ":443/cashboxApi/backend/v1/cashbox/"
        self.V2_URL_TAIL = ":443/cashboxApi/backend/v2/cashbox/"
        self.session = self.start_session()
        
    def start_session(self):
        session = requests.session()
        session.auth = ('admin', 'psw')
        session.headers['Accept'] = "application/json"
        return session

    def gen_token(self, cashbox_id, backend_url, attempts = 5):
        self.session.headers['Content-Type'] = "application/json"
        url = backend_url + self.V1_URL_TAIL + f"{cashbox_id}/resetPassword"
        for i in range(attempts):
            token = str(random.randrange(11111111, 99999999))
            data = json.dumps({"Token" : token})
            result = self.session.post(url, data = data)
            print(f"Результат запроса {cashbox_id}/resetPassword: {result}")
            if result.ok: 
                pyperclip.copy(f"{token}")
                break

    def change_hardware_settings(self, cashbox_id, kkt: list, pos: list, backend_url):
        settings = self.get_cashbox_settings_json(cashbox_id, backend_url)
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

        self.post_cashbox_settings(cashbox_id, backend_settings, backend_url, True)
        self.post_cashbox_settings(cashbox_id, app_settings, backend_url, False)
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

    def get_cashbox_settings_json(self, cashboxId, backendUrl):
        response = self.session.get(backendUrl + self.V2_URL_TAIL + f'{cashboxId}/settings')
        return json.loads(response.content)

    def post_cashbox_settings(self, cashboxId, settings, backend_url, backend = True):
        settings_type = "backend" if backend else "app"
        self.session.headers['Content-Type'] = "application/json"
        result = self.session.post(backend_url + self.V2_URL_TAIL + f"{cashboxId}/settings/" + f"{settings_type}", data = json.dumps(settings))
        print(result)

    def flip_settings(self, settings, settings_name, settings_type = "backendSettings"):
        settings["settings"][settings_type][settings_name] = not settings["settings"][settings_type][settings_name]
        result = {}
        result["settings"] = settings["settings"][settings_type]
        result["previousVersion"] = settings["versions"]["backendVersion"]
        return result