import logging
import os
import datetime
import sys
import ctypes
import uuid
from helpers.fileshelper import * 
from helpers.nethelper import *
import pyperclip
import keyboard
from console import fg, bg, fx
import console.utils

ENTITIES = ["stage", "cashbox", "cashboxId", "delete", "gen", "shift", "flip_settings", "receipt", "setKkt", "scanner"]
PROG_NAME = "kmk_scripts"
KKT = ["None", "Atol", "VikiPrint", "Shtrih"]
POS = ["None", "External", "Inpas", "Ingenico", "Sberbank"]
MARKTYPES = ["Excise", "Tabak", "Cis", "Milk"]
ERROR = (bg.lightred + fg.black)("ОШИБКА")
HELLO = (bg.green + fg.black)("Горячие клавиши - в вашем распоряжении")
file_change_style = fg.lightblack + fx.italic

def turn_cashbox_service(shouldStop=True):
    """ Даёт команду службе кассы: stop или start """
    success = change_cashbox_service_state(shouldStop)
    if (success):
        print(f"Вы {'остановили' if shouldStop else 'запустили'} службу SKBKontur.Cashbox")
    else: 
        print(f"Не удалось {'остановить' if shouldStop else 'запустить'} службу SKBKontur.Cashbox")
def set_stage(stageNumber):
    """ Выставляем в конфиге адрес, который соответствует первому или второму стейджу
    А цифре 9 соответствуют продовые настройки
    """
    set_staging(int(stageNumber))
    print(f"Касса готова к работе с {stageNumber + ' стейджем' if stageNumber != '9' else ' продом'}")

def paste_cashboxid_in_clipboard():
    cashboxId = get_cashbox_id()
    pyperclip.copy(cashboxId)
    print(f"В вашем буфере обмена — текущий cashboxId: \n{cashboxId}")

def cache_cashboxid_from_clipboard():
    cashboxId = pyperclip.paste()
    cache_in_local_json("cashboxId", cashboxId)
    print(f"Вы вставили из буфера в data.json cashboxId = \n{cashboxId}")

def delete_cashbox(delete_db: bool, delete_cashbox: bool):
    change_cashbox_service_state(True)
    cashboxPath = find_cashbox_path()
    if delete_cashbox:
        binPath = os.path.join(cashboxPath, "bin")
        delete_folder(binPath)
        print("Приложение кассы удалено")
    if delete_db:
        dbPath = os.path.join(cashboxPath, "db")
        delete_folder(dbPath)
        print("БД кассы удалена")
def gen_token():
    cashboxId = get_cashbox_id()
    backendUrl = get_backend_url_from_config(find_config_path())
    gen_token_CS(start_session(), cashboxId, backendUrl)
    print(f"В вашем буфере обмена - новый токен для кассы: \n{cashboxId}")
def gen_guid():
    guid = str(uuid.uuid4())
    pyperclip.copy(guid)
    print(f"В вашем буфере - guid: \n{guid}")
def set_shift_duration(durationInHours=24):
    con = set_db_connection()
    shift = json.loads(get_last_shift_from_db(con))
    shift["openInfo"]["openDateTime"] = str(datetime.datetime.now() - datetime.timedelta(hours = durationInHours))
    edit_shift_in_db(con, json.dumps(shift), True)
    print(f"Длительность текущей смены = {durationInHours}")
def unreg_last_receipt():
    con = set_db_connection()
    (id, shiftId, number, content) = get_last_receipt(con)
    receipt = json.loads(content)
    receipt["kkmRegistrationStatus"] = "Error"
    receipt["correctionReceiptId"] = None
    update_receipt_content(con, json.dumps(receipt), id, True)
    print(f"Последний чек продажи стал незареганным. \nОн на сумму = {receipt['contributedSum']}")
def flip_settings(settings_name:string):
    cashboxId = get_cashbox_id()
    session = start_session()
    backendUrl = get_backend_url_from_config(find_config_path())
    settings = get_cashbox_settings_json(session, cashboxId, backendUrl)
    flippedSettings = flip_settings_CS(settings, settings_name)
    post_cashbox_settings(session, cashboxId, flippedSettings, backendUrl)
    print(f'Настройка {settings_name} теперь = {settings["settings"]["backendSettings"][settings_name]}')
def set_kkms():
    print("""Выберите 1 или 2 ККТ: первая для ЮЛ с ИНН = 6699000000, вторая - для ЮЛ с ИНН = 992570272700
    \n0. None \n1. Atol \n2. VikiPrint\n3. Shtrih
    \nНапример, если ввели "1" - Атол в режиме 1 ЮЛ, если "2 3" - Вики и Штрих в режиме 2ЮЛ\n""")
    kktNumbers = list(map(int, input().strip().split()))
    print("""\nВыберите 1 или 2 терминала: 
    \n0. None \n1. External \n2. Inpas\n3. Ingenico \n4. Sberbank\n""")
    posNumbers = list(map(int, input().strip().split()))
    if kktNumbers.count == 0 or posNumbers.count == 0:
        print("Вы не указали ККТ или эквайринги")
    elif kktNumbers.count != posNumbers.count:
        print("Вы указали разное количество ККТ и терминалов")
    else:
        change_cashbox_service_state(True)
        kkt = []
        pos = []
        for i in range (len(kktNumbers)):
            kkt.append(KKT[kktNumbers[i]])
            pos.append(POS[posNumbers[i]])
        cashboxId = get_cashbox_id()
        backendUrl = get_backend_url_from_config(find_config_path())
        le = change_hardware_settings(start_session(), cashboxId, kkt, pos, backendUrl)
        set_legalentityid_in_products(le, True)
        change_cashbox_service_state(False)
        print(f"Ваши ККТ: {', '.join(kkt) }\nВаши терминалы: {', '.join(pos)}")
def use_scanner(mode="normal"):
    if mode == "quiet":
        paste_mark_in_scanner_mode("", False, True)
    else:
        print("Какую марку вставить? Введите число: \n \n 0. Из буфера \n 1. Акцизную \n 2. Сигарет \n 3. Шин, духов, одежды, обуви, фото, воды \n 4. Молока")
        number = int(input().strip())
        if number == 0:
            paste_mark_in_scanner_mode("", True, False)
        else: 
            paste_mark_in_scanner_mode(MARKTYPES[number - 1], False, False)

def main():
    print(HELLO)
    keyboard.add_hotkey("alt+5", lambda: turn_cashbox_service(True))
    keyboard.add_hotkey("alt+6", lambda: turn_cashbox_service(False))
    keyboard.add_hotkey("alt+1", lambda: set_stage("1"))
    keyboard.add_hotkey("alt+2", lambda: set_stage("2"))
    keyboard.add_hotkey("alt+9", lambda: set_stage("9"))
    keyboard.add_hotkey("alt+p", lambda: cache_cashboxid_from_clipboard())
    keyboard.add_hotkey("alt+i", lambda: paste_cashboxid_in_clipboard())
    keyboard.add_hotkey("alt+d", lambda: delete_cashbox(True, False))
    keyboard.add_hotkey("alt+c", lambda: delete_cashbox(False, True))
    keyboard.add_hotkey("alt+shift+c", lambda: delete_cashbox(True, True))
    keyboard.add_hotkey("alt+t", lambda: gen_token())
    keyboard.add_hotkey("alt+g", lambda: gen_guid())
    keyboard.add_hotkey("alt+-", lambda: set_shift_duration())
    keyboard.add_hotkey("alt+e", lambda: unreg_last_receipt()) 
    keyboard.add_hotkey("alt+o", lambda: flip_settings("moveRemainsToNextShift"))
    keyboard.add_hotkey("alt+a", lambda: flip_settings("prepaidEnabled"))
    keyboard.add_hotkey("alt+k", lambda: set_kkms())   
    keyboard.add_hotkey('alt+s', lambda: use_scanner())
    keyboard.add_hotkey('alt+shift+s', lambda: use_scanner("quiet"))
    keyboard.add_abbreviation('adm1', 'https://market.testkontur.ru/AdminTools')
    keyboard.add_abbreviation('adm2', 'https://market-dev.testkontur.ru/AdminTools')
    keyboard.add_abbreviation('csadm1', 'https://market.testkontur.ru/cashboxApi/admin/web/cashbox/')
    keyboard.add_abbreviation('csadm2', 'https://market-dev.testkontur.ru/cashboxApi/admin/web/cashbox/')
    keyboard.add_abbreviation('apidoc', 'https://developer.kontur.ru/')
    keyboard.wait('alt+esc')

if __name__ == "__main__":
    main()