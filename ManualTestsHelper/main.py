import argparse
import pyperclip
import os
from helpers.fileshelper import * 
from helpers.nethelper import *

def startParser():
    parser = argparse.ArgumentParser(description="Manage SKBKontur.Cashbox service, change data in local DB and in remote Cashbox Server")
    parser.add_argument("command", help = "the command")
    parser.add_argument("value", help = "the value")
    return parser

args = startParser().parse_args()

match args.command:
    case "stage":
        setStaging(int(args.value))
    case "cashbox":
        changeCashboxServiceState(args.value)
    case "cashboxId":
        if args.value == "paste":
            writeJsonValue("cashboxId", pyperclip.paste())
        elif args.value == "copy":
            pyperclip.copy(getCashboxId())
    case "delete":
        changeCashboxServiceState("stop")
        cashboxPath = findCashboxPath()
        if args.value == "cashbox":
            deleteFolder(cashboxPath)
        elif args.value == "db":
            dbPath = os.path.join(cashboxPath, "db")
            deleteFolder(dbPath)
    case "token":
        genToken(startSession(), getCashboxId(), int(args.value))
    case "shift":
        if args.value == "set24":
            con = setDbConnection()
            shift = json.loads(getLastShiftFromDb(con))
            shift["openInfo"]["openDateTime"] = "2022-11-03 22:39:30.5000103"
            editShiftInDB(con, json.dumps(shift), True)
    case "settings":
        if args.value == "remains":
            cashboxId = getCashboxId()
            session = startSession()
            settings = getCashoxSettingsJson(session, cashboxId)
            flippedSettings = flipBoolSettings(settings, "moveRemainsToNextShift")
            postCashboxSettings(session, cashboxId, flippedSettings)
    case "receipt":
        if args.value == "regError":
            con = setDbConnection()
            (id, shiftId, number, content) = getLastReceipt(con)
            receipt = json.loads(content)
            receipt["kkmRegistrationStatus"] = "Error"
            receipt["correctionReceiptId"] = None
            updateReceiptContent(con, json.dumps(receipt), id, True)
    case _: 
        print ("Неизвестная команда")