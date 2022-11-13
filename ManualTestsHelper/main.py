import argparse
import pyperclip
import os
from helpers.fileshelper import * 
from helpers.nethelper import *

ENTITIES = ["stage", "cashbox", "cashboxId", "delete", "token", "shift", "settings", "receipt"]

def startParser():
    parser = argparse.ArgumentParser(description="Manage SKBKontur.Cashbox service, change data in local DB and in remote Cashbox Server")
    parser.add_argument("entity", help = "the entity", choices=ENTITIES)
    parser.add_argument("action", help = "the action")
    return parser

args = startParser().parse_args()

match args.entity:
    case "stage":
        setStaging(int(args.action))
    case "cashbox":
        changeCashboxServiceState(args.action)
    case "cashboxId":
        if args.action == "paste":
            writeJsonValue("cashboxId", pyperclip.paste())
        elif args.action == "copy":
            pyperclip.copy(getCashboxId())
    case "delete":
        changeCashboxServiceState("stop")
        cashboxPath = findCashboxPath()
        if args.action == "cashbox":
            deleteFolder(cashboxPath)
        elif args.action == "db":
            dbPath = os.path.join(cashboxPath, "db")
            deleteFolder(dbPath)
    case "token":
        genToken(startSession(), getCashboxId(), int(args.action))
    case "shift":
        if args.action == "set24":
            con = setDbConnection()
            shift = json.loads(getLastShiftFromDb(con))
            shift["openInfo"]["openDateTime"] = "2022-11-03 22:39:30.5000103"
            editShiftInDB(con, json.dumps(shift), True)
    case "settings":
        if args.action == "remains":
            cashboxId = getCashboxId()
            session = startSession()
            settings = getCashoxSettingsJson(session, cashboxId)
            flippedSettings = flipBoolSettings(settings, "moveRemainsToNextShift")
            postCashboxSettings(session, cashboxId, flippedSettings)
    case "receipt":
        if args.action == "regError":
            con = setDbConnection()
            (id, shiftId, number, content) = getLastReceipt(con)
            receipt = json.loads(content)
            receipt["kkmRegistrationStatus"] = "Error"
            receipt["correctionReceiptId"] = None
            updateReceiptContent(con, json.dumps(receipt), id, True)
    case _: 
        print ("Для команды не прописано действие")

