import argparse
import logging
import os
import sys
import ctypes
import uuid
from helpers.fileshelper import * 
from helpers.nethelper import *
import pyperclip
import keyboard
  
ENTITIES = ["stage", "cashbox", "cashboxId", "delete", "gen", "shift", "flip_settings", "receipt", "setKkt", "scanner"]
PROG_NAME = "kmk_scripts"
KKT = ["None", "Atol", "VikiPrint", "Shtrih"]
POS = ["None", "External", "Inpas", "Ingenico", "Sberbank"]
MARKTYPES = ["Excise", "Tabak", "Cis", "Milk"]

def ruleService(shouldStop = True):
    success = changeCashboxServiceState(shouldStop)
    if (success):
        printMsg(PROG_NAME, f"Вы {'остановили' if shouldStop else 'запустили'} службу SKBKontur.Cashbox")
    else: 
        printMsg(PROG_NAME, f"Не удалось {'остановить' if shouldStop else 'запустить'} службу SKBKontur.Cashbox")
def setStage(stageNumber):
    setStaging(int(stageNumber))
    printMsg(PROG_NAME, f"Касса готова к работе с {stageNumber + 'стейджем' if stageNumber != '9' else 'продом'}")
def useCashboxId(shouldGet = True):
    if shouldGet:
        cashboxId = getCashboxId()
        pyperclip.copy(cashboxId)
        printMsg(PROG_NAME, f"В вашем буфере обмена — текущий cashboxId: \n{cashboxId}")
    else: 
        cashboxId = pyperclip.paste()
        writeJsonValue("cashboxId", cashboxId)
        printMsg(PROG_NAME, f"Вы вставили из буфера в data.json cashboxId = \n{cashboxId}")
def delete(objectName):
    changeCashboxServiceState(True)
    cashboxPath = findCashboxPath()
    if objectName == "cashbox":
        binPath = os.path.join(cashboxPath, "bin")
        deleteFolder(binPath)
        printMsg(PROG_NAME, "Вы удалили КМК, но оставили БД")
    elif objectName == "db":
        dbPath = os.path.join(cashboxPath, "db")
        deleteFolder(dbPath)
        printMsg(PROG_NAME, "Вы удалили БД кассы")
    elif objectName == "cashbox_and_db":
        deleteFolder(cashboxPath)
        printMsg(PROG_NAME, "Вы удалили КМК и БД")
    #раздвоилась функция
def generateToken():
    cashboxId = getCashboxId()
    backendUrl = getBackendUrlFromConfig(findConfigPath())
    genToken(startSession(), cashboxId, backendUrl)
    printMsg(PROG_NAME, f"В вашем буфере обмена - новый токен для кассы: \n{cashboxId}")
def generateGuid():
    guid = str(uuid.uuid4())
    pyperclip.copy(guid)
    printMsg(PROG_NAME, f"В вашем буфере - guid: \n{guid}")
def changeShift(durationInHours = 24):
    # вычислять дату
    con = setDbConnection()
    shift = json.loads(getLastShiftFromDb(con))
    shift["openInfo"]["openDateTime"] = "2022-11-03 22:39:30.5000103"
    editShiftInDB(con, json.dumps(shift), True)
    printMsg(PROG_NAME, "Теперь текущая смена больше 24 часов")
def unregLastReceipt():
    con = setDbConnection()
    (id, shiftId, number, content) = getLastReceipt(con)
    receipt = json.loads(content)
    receipt["kkmRegistrationStatus"] = "Error"
    receipt["correctionReceiptId"] = None
    updateReceiptContent(con, json.dumps(receipt), id, True)
    printMsg(PROG_NAME, f"Последний чек продажи стал незареганным. \nОн на сумму = {receipt['contributedSum']}")
def flipSettings(settingsName):
    cashboxId = getCashboxId()
    session = startSession()
    backendUrl = getBackendUrlFromConfig(findConfigPath())
    settings = getCashoxSettingsJson(session, cashboxId, backendUrl)
    flippedSettings = flipBoolSettings(settings, settingsName)
    postCashboxSettings(session, cashboxId, flippedSettings, backendUrl)
    printMsg(PROG_NAME, f'Настройка {settingsName} теперь = {settings["settings"]["backendSettings"][settingsName]}')
def setKkt():
    print("""Выберите 1 или 2 ККТ: первая для ЮЛ с ИНН = 6699000000, вторая - для ЮЛ с ИНН = 992570272700
    \n0. None \n1. Atol \n2. VikiPrint\n3. Shtrih
    \nНапример, если ввели "1" - Атол в режиме 1 ЮЛ, если "2 3" - Вики и Штрих в режиме 2ЮЛ\n""")
    kktNumbers = list(map(int, input().strip().split()))
    print("""\nВыберите 1 или 2 терминала: 
    \n0. None \n1. External \n2. Inpas\n3. Ingenico \n4. Sberbank\n""")
    posNumbers = list(map(int, input().strip().split()))
    if kktNumbers.count == 0:
        printMsg(PROG_NAME, "Вы не написали названия ККТ. Запустите скрипт снова")
    else:
        changeCashboxServiceState(True)
        kkt = []
        pos = []
        for i in range (len(kktNumbers)):
            kkt.append(KKT[kktNumbers[i]])
            pos.append(POS[posNumbers[i]])
        cashboxId = getCashboxId()
        backendUrl = getBackendUrlFromConfig(findConfigPath())
        le = setKktAndPos(startSession(), cashboxId, kkt, pos, backendUrl)
        setLeInProducts(le, True)
        changeCashboxServiceState(False)
        printMsg(PROG_NAME, f"Ваши ККТ: {', '.join(kkt) }\nВаши терминалы: {', '.join(pos)}")
def useScanner(mode = "normal"):
    if mode == "quiet":
        pasteMarkLikeByScanner("", False, True)
    else:
        print("Какую марку вставить? Введите число: \n \n 0. Из буфера \n 1. Акцизную \n 2. Сигарет \n 3. Шин, духов, одежды, обуви, фото, воды \n 4. Молока")
        number = int(input().strip())
        if number == 0:
            pasteMarkLikeByScanner("", True, False)
        else: 
            pasteMarkLikeByScanner(MARKTYPES[number - 1], False, False)

# @main_requires_admin(return_output=True)
def main():
    print("Скрипты запущены, горячие клавиши уже работают")
    keyboard.add_hotkey("alt+shift+down", lambda: ruleService(True))
    keyboard.add_hotkey("alt+shift+up", lambda: ruleService(False))
    keyboard.add_hotkey("alt+1", lambda: setStage("1"))
    keyboard.add_hotkey("alt+2", lambda: setStage("2"))
    keyboard.add_hotkey("alt+9", lambda: setStage("9"))
    keyboard.add_hotkey("alt+p", lambda: useCashboxId(False))
    keyboard.add_hotkey("alt+i", lambda: useCashboxId(True))
    keyboard.add_hotkey("alt+d", lambda: delete("db"))
    keyboard.add_hotkey("alt+c", lambda: delete("cashbox"))
    keyboard.add_hotkey("alt+shift+c", lambda: delete("cashbox_and_db"))
    keyboard.add_hotkey("alt+t", lambda: generateToken())
    keyboard.add_hotkey("alt+g", lambda: generateGuid())
    keyboard.add_hotkey("alt+-", lambda: changeShift())
    keyboard.add_hotkey("alt+e", lambda: unregLastReceipt()) 
    keyboard.add_hotkey("alt+o", lambda: flipSettings("moveRemainsToNextShift"))
    keyboard.add_hotkey("alt+a", lambda: flipSettings("prepaidEnabled"))
    keyboard.add_hotkey("alt+k", lambda: setKkt())   
    keyboard.add_hotkey('alt+s', lambda: useScanner())
    keyboard.add_hotkey('alt+shift+s', lambda: useScanner("quiet"))
    keyboard.add_abbreviation('adm1', 'https://market.testkontur.ru/AdminTools')
    keyboard.add_abbreviation('adm2', 'https://market-dev.testkontur.ru/AdminTools')
    keyboard.add_abbreviation('csadm1', 'https://market.testkontur.ru/cashboxApi/admin/web/cashbox/')
    keyboard.add_abbreviation('csadm2', 'https://market-dev.testkontur.ru/cashboxApi/admin/web/cashbox/')
    keyboard.add_abbreviation('apidoc', 'https://developer.kontur.ru/')
    keyboard.wait('alt+esc')

if __name__ == "__main__":
    main()