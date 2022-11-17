import argparse
import pyperclip
import os
import uuid
from helpers.fileshelper import * 
from helpers.nethelper import *


ENTITIES = ["stage", "cashbox", "cashboxId", "delete", "gen", "shift", "flip_settings", "receipt", "set2LE"]
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
            printMsg(PROG_NAME, f"Вы вставили из буфера в data.json cashboxId = \n{cashboxId}")
        elif args.action == "copy":
            cashboxId = getCashboxId()
            pyperclip.copy(cashboxId)
            printMsg(PROG_NAME, f"В вашем буфере обмена — текущий cashboxId: \n{cashboxId}")
    case "delete":
        changeCashboxServiceState("stop")
        cashboxPath = findCashboxPath()
        if args.action == "cashbox":
            deleteFolder(cashboxPath)
            printMsg(PROG_NAME, "Вы удалили кассу с ПК")
        elif args.action == "db":
            dbPath = os.path.join(cashboxPath, "db")
            deleteFolder(dbPath)
            printMsg(PROG_NAME, "Вы удалили БД кассы")
    case "gen":
        if args.action == "token":
            cashboxId = getCashboxId()
            genToken(startSession(), cashboxId)
            printMsg(PROG_NAME, f"В вашем буфере обмена - новый токен для кассы: \n{cashboxId}")
        elif args.action == "guid":
            guid = str(uuid.uuid4())
            pyperclip.copy(guid)
            printMsg(PROG_NAME, f"В вашем буфере - guid: \n{guid}")
    case "shift":
        if args.action == "set24":
            con = setDbConnection()
            shift = json.loads(getLastShiftFromDb(con))
            shift["openInfo"]["openDateTime"] = "2022-11-03 22:39:30.5000103"
            editShiftInDB(con, json.dumps(shift), True)
            printMsg(PROG_NAME, "Теперь текущая смена больше 24 часов")
    case "flip_settings":
        cashboxId = getCashboxId()
        session = startSession()
        settings = getCashoxSettingsJson(session, cashboxId)
        flippedSettings = flipBoolSettings(settings, args.action)
        postCashboxSettings(session, cashboxId, flippedSettings)
        printMsg(PROG_NAME, f'Настройка {args.action} теперь = {settings["settings"]["backendSettings"][args.action]}')
    case "receipt":
        if args.action == "regError":
            con = setDbConnection()
            (id, shiftId, number, content) = getLastReceipt(con)
            receipt = json.loads(content)
            receipt["kkmRegistrationStatus"] = "Error"
            receipt["correctionReceiptId"] = None
            updateReceiptContent(con, json.dumps(receipt), id, True)
            printMsg(PROG_NAME, f"Последний чек продажи стал незареганным. \nОн на сумму = {receipt['contributedSum']}")
    case "set2LE":
        kkt1 = ""
        kkt2 = ""
        if args.action == "sasha":
            kkt1 = "Atol"
            kkt2 = "Atol"
        elif args.action == "slava":
            kkt1 = "VikiPrint"
            kkt2 = "Atol"
        elif args.action == "misha":
            kkt1 = "VikiPrint"
            kkt2 = "Shtrih"
        elif args.action == "none":
            kkt1 = "None"
            kkt2 = "None"
        prepSettingsFor2UL(startSession(), getCashboxId(), kkt1, kkt2)
        printMsg(PROG_NAME, f"Вы переключили кассу в режим 2ЮЛ\nККТ: {kkt1} и {kkt2}")
    case _: 
        print ("Для команды не прописано действие")