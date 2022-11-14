import argparse
import pyperclip
import os
from helpers.fileshelper import * 
from helpers.nethelper import *

ENTITIES = ["stage", "cashbox", "cashboxId", "delete", "token", "shift", "settings", "receipt"]
PROG_NAME = "kmk_scripts"

def startParser():
    parser = argparse.ArgumentParser(description="Manage SKBKontur.Cashbox service, change data in local DB and in remote Cashbox Server", prog = PROG_NAME)
    parser.add_argument("entity", help = "the entity", choices=ENTITIES)
    parser.add_argument("action", help = "the action")
    return parser

args = startParser().parse_args()

match args.entity:
    case "stage":
        setStaging(int(args.action))
        printMsg(PROG_NAME, f"Касса готова к работе с {args.action + ' стейджем' if args.action != '9' else 'продом'}")
    case "cashbox":
        changeCashboxServiceState(args.action)
        printMsg(PROG_NAME, f"Вы {'остановили' if args.action == 'stop' else 'запустили'} службу SKBKontur.Cashbox")
    case "cashboxId":
        if args.action == "paste":
            cashboxId = pyperclip.paste()
            writeJsonValue("cashboxId", cashboxId)
            printMsg(PROG_NAME, f"Вы вставили из буфера в data.json cashboxId = {cashboxId}")
        elif args.action == "copy":
            cashboxId = getCashboxId()
            pyperclip.copy(cashboxId)
            printMsg(PROG_NAME, f"В вашем буфере обмена — текущий cashboxId: {cashboxId}")
    case "delete":
        changeCashboxServiceState("stop")
        cashboxPath = findCashboxPath()
        if args.action == "cashbox":
            deleteFolder(cashboxPath)
            printMsg(PROG_NAME, "Вы удалили БД кассы")
        elif args.action == "db":
            dbPath = os.path.join(cashboxPath, "db")
            deleteFolder(dbPath)
            printMsg(PROG_NAME, "Вы удалили кассу с ПК")
    case "token":
        genToken(startSession(), getCashboxId(), int(args.action))
        printMsg(PROG_NAME, "Новый токен - в вашем буфере обмена")
    case "shift":
        if args.action == "set24":
            con = setDbConnection()
            shift = json.loads(getLastShiftFromDb(con))
            shift["openInfo"]["openDateTime"] = "2022-11-03 22:39:30.5000103"
            editShiftInDB(con, json.dumps(shift), True)
            printMsg(PROG_NAME, "Теперь текущая смена больше 24 часов")
    case "settings":
        if args.action == "remains":
            cashboxId = getCashboxId()
            session = startSession()
            settings = getCashoxSettingsJson(session, cashboxId)
            flippedSettings = flipBoolSettings(settings, "moveRemainsToNextShift")
            postCashboxSettings(session, cashboxId, flippedSettings)
            printMsg(PROG_NAME, f"Настройка переноса остатков теперь = {settings['settings']['backendSettings']['moveRemainsToNextShift']}")
    case "receipt":
        if args.action == "regError":
            con = setDbConnection()
            (id, shiftId, number, content) = getLastReceipt(con)
            receipt = json.loads(content)
            receipt["kkmRegistrationStatus"] = "Error"
            receipt["correctionReceiptId"] = None
            updateReceiptContent(con, json.dumps(receipt), id, True)
            printMsg(PROG_NAME, f"Последний чек продажи стал незареганным. Он на сумму = {receipt['contributedSum']}") # дописать сумму
    case _: 
        print ("Для команды не прописано действие")

