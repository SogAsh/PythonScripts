import argparse
import pyperclip
import os
import uuid
from helpers.fileshelper import * 
from helpers.nethelper import *

ENTITIES = ["stage", "cashbox", "cashboxId", "delete", "gen", "shift", "flip_settings", "receipt", "setKkt"]
PROG_NAME = "kmk_scripts"
KKT = ["None", "Atol", "VikiPrint", "Shtrih"]
POS = ["None", "External", "Inpas", "Ingenico", "Sberbank"]

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
    case "setKkt":
        print("""Какие ККТ выбрать в настройках? Введите один или два номера через пробел: 
        \n0. None \n1. Atol \n2. VikiPrint\n3. Shtrih
        \nНапример, чтобы включить режим 2ЮЛ с Атолом и Штрихом, введите: 1 3\n""")
        kktNumbers = list(map(int, input().strip().split()))
        print("""\nКакие выбрать терминалы? Введите один или два номера через пробел: 
        \n0. None \n1. External \n2. Inpas\n3. Ingenico \n4. Sberbank\n""")
        posNumbers = list(map(int, input().strip().split()))
        if kktNumbers.count == 0:
            printMsg(PROG_NAME, "Вы не написали названия ККТ")
        else:
            kkt = []
            pos = []
            for i in range (len(kktNumbers)):
                kkt.append(KKT[kktNumbers[i]])
                pos.append(POS[posNumbers[i]])

            setKktAndPos(startSession(), getCashboxId(), kkt, pos)
            printMsg(PROG_NAME, f"Ваши ККТ: {', '.join(kkt) }\nВаши терминалы: {', '.join(pos)}")
    case _: 
        print ("Для команды не прописано действие")