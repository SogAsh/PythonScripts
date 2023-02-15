import os
import datetime
from tkinter import COMMAND
import uuid
import sys
import ctypes
import json
from helpers.fileshelper import Mark, DB, OS 
from helpers.nethelper import CS
import pyperclip
import keyboard
from console import fg, bg, fx
import console.utils

KKT = ["None", "Atol", "VikiPrint", "Shtrih"]
POS = ["None", "External", "Inpas", "Ingenico", "Sberbank"]
MARKTYPES = ["Excise", "Tabak", "Cis", "Milk"]
ERR = bg.lightred + fg.black
YO = bg.green + fg.black
SUCCESS = lambda: print(YO("\nСкрипт завершился успешно\n\n"))
file_change_style = fg.lightblack + fx.italic

class Command:


    @staticmethod
    def name():
        raise NotImplementedError()

    @staticmethod
    def description():
        raise NotImplementedError()

    @staticmethod
    def help():
        raise NotImplementedError()

    @staticmethod
    def execute():
        raise NotImplementedError()

class TurnOffCashbox(Command):


    @staticmethod
    def name():
        return "turn"  

    def description():
        return "Отключает (1) или включает (0) службу кассы"

    def help(message = ""):
        print(message + "\n" + f"У команды '{TurnOffCashbox.name()}' один аргумент: " 
        + "1 - остановить службу, 0 - запустить")

    def execute(*params):
        if (len(params) != 1):
            TurnOffCashbox.help(ERR("Неверное количество параметров"))
            return
        if (params[0] not in ["0", "1"]):
            TurnOffCashbox.help(ERR("Неверный аргумент"))
            return
        should_stop = bool(int(params[0]))
        success = OS.change_cashbox_service_state(should_stop)
        if success:
            print(f"Вы {'остановили' if should_stop else 'запустили'} службу SKBKontur.Cashbox") 
            SUCCESS()
        else: 
            print(f"Не удалось {'остановить' if should_stop else 'запустить'} службу SKBKontur.Cashbox")

class SetStage(Command):


    @staticmethod
    def name():
        return "stage"

    def description():
        return "Выбор стейджа для кассы: 1 или 2"

    def help(message):
        print(message + "\n" + f"У команды '{SetStage.name()}' один аргумент: " 
        + "1 - первый стейдж, 2 - второй, 9 - прод")

    def execute(*params):
        if (len(params) != 1):
            SetStage.help(ERR("Неверное количество параметров"))
            return
        if (params[0] not in ["0", "1", "9"]):
            SetStage.help(ERR("Неверный аргумент"))
            return
        stage = params[0]
        OS.set_staging(int(stage))
        print(f"Касса готова к работе с {stage + ' стейджем' if stage != '9' else ' продом'}")
        SUCCESS() 

class GetCashboxId(Command):


    @staticmethod
    def name():
        return "getid"

    def description():
        return "Скопировать текущий cashboxId в буфер"

    def help():
        return "В буфер обмена попадает текущий cashboxId - он достаётся из БД"

    def execute():
        cashboxId = DB().get_cashbox_id(True)
        pyperclip.copy(cashboxId)
        print(f"В вашем буфере обмена — текущий cashboxId: \n{cashboxId}")
        SUCCESS()

class CacheCashboxId(Command):


    @staticmethod
    def name():
        return "setid"

    def description():
        return "Вставить cashboxId из буфера в data.json"

    def execute():
        cashboxId = pyperclip.paste()
        OS.cache_in_local_json("cashboxId", cashboxId)
        print(f"Вы вставили из буфера в data.json cashboxId = \n{cashboxId}")
        SUCCESS()

class DeleteCashbox(Command):


    @staticmethod
    def name():
        return "del"

    def description():
        return "Удалить кассу (0 1) или БД (1 0)"

    def help(message):
        print(message + "\n" + f"У команды '{DeleteCashbox.name()}' два аргумента: " 
        + "1. 1 - удалить БД, 0 - не удалять \n 2. 1 - удалить КМК, 0 - не удалять")

    def execute(*params):
        if (len(params) != 2):
            DeleteCashbox.help(ERR("Неверное количество параметров"))
            return
        if (params[0] not in ["0", "1"] or params[1] not in ["0", "1"]):
            DeleteCashbox.help(ERR("Неверный аргумент"))
            return
        delete_db = bool(int(params[0]))
        delete_cashbox = bool(int(params[1]))
        OS.change_cashbox_service_state(True)
        cashboxPath = OS.find_cashbox_path()
        if delete_db:
            OS.delete_folder(os.path.join(cashboxPath, "db"))
        if delete_cashbox:
            OS.delete_folder(os.path.join(cashboxPath, "bin"))
        if delete_cashbox:
            print("Приложение кассы удалено")
        if delete_db:
            print("БД кассы удалена")
        SUCCESS()

class GenToken(Command):


    @staticmethod
    def name():
        return "token"

    def description():
        return "Сгенерировать токен для кассы"

    def execute():
        cashboxId = DB().get_cashbox_id(True)
        backendUrl = OS.get_backend_url_from_config(OS.find_config_path())
        CS().gen_token_CS(cashboxId, backendUrl)
        print(f"В вашем буфере обмена - новый токен для кассы: \n{cashboxId}")
        SUCCESS()

class GenGuid(Command):


    @staticmethod
    def name():
        return "guid"

    def description():
        return "Сгенерировать произвольный гуид"

    def execute():
        guid = str(uuid.uuid4())
        pyperclip.copy(guid)
        print(f"В вашем буфере - guid: \n{guid}")
        SUCCESS()

class SetShiftDuration(Command):


    @staticmethod
    def name():
        return "shift"

    def description():
        return "Установить длительность смены в часах"

    def help(message):
        print(message + "\n" + f"У команды '{SetShiftDuration.name()}' один аргумент: " 
        + "желаемое количество часов в смене")

    def execute(*params):
        if (len(params) != 1):
            SetShiftDuration.help(ERR("Неверное количество параметров"))
            return
        duration_in_hours = int(params[0])
        db = DB()
        shift = json.loads(db.get_last_shift_from_db())
        shift["openInfo"]["openDateTime"] = str(datetime.datetime.now() - datetime.timedelta(hours = duration_in_hours))
        db.edit_shift_in_db(json.dumps(shift), True)
        print(f"Длительность текущей смены = {duration_in_hours}")
        SUCCESS()

class UnregLastReceipt(Command):


    @staticmethod
    def name():
        return "unreg"

    def description():
        return "Сделать последнему чеку статус = Error"

    def execute():
        db = DB()
        (id, shiftId, number, content) = db.get_last_receipt()
        receipt = json.loads(content)
        receipt["kkmRegistrationStatus"] = "Error"
        receipt["correctionReceiptId"] = None
        db.update_receipt_content(json.dumps(receipt), id, True)
        print(f"Последний чек продажи стал незареганным. \nОн на сумму = {receipt['contributedSum']}")
        SUCCESS()

class FlipSettings(Command):


    @staticmethod
    def name():
        return "settings"

    def description():
        return "Изменить буллевую настройку"

    def help(message):
        print(message + "\n" + f"У команды '{FlipSettings.name()}' один аргумент: " 
        + "название настройки. Например, moveRemainsToNextShift или prepaidEnabled")

    def execute(*params):
        if (len(params) != 1):
            FlipSettings.help(ERR("Неверное количество параметров"))
            return
        settings_name = params[0]
        cashboxId = DB().get_cashbox_id(True)
        cs = CS()
        backendUrl = OS.get_backend_url_from_config(OS.find_config_path())
        settings = cs.get_cashbox_settings_json(cashboxId, backendUrl)
        flippedSettings = cs.flip_settings_CS(settings, settings_name)
        cs.post_cashbox_settings(cashboxId, flippedSettings, backendUrl)
        print(f'Настройка {settings_name} теперь = {settings["settings"]["backendSettings"][settings_name]}')
        SUCCESS()

class SetHardwareSettings(Command):


    @staticmethod
    def name():
        return "kkms"

    def description():
        return "Выбрать 1-2 ККТ и терминала"

    def execute():
        print("""Выберите 1 или 2 ККТ: первая для ЮЛ с ИНН = 6699000000, вторая - для ЮЛ с ИНН = 992570272700
        \n0. None \n1. Atol \n2. VikiPrint\n3. Shtrih
        \nНапример, если ввели "1" - Атол в режиме 1 ЮЛ, если "2 3" - Вики и Штрих в режиме 2ЮЛ\n""")
        kktNumbers = list(map(int, input().strip().split()))
        print("""\nВыберите 1 или 2 терминала: 
        \n0. None \n1. External \n2. Inpas\n3. Ingenico \n4. Sberbank\n""")
        posNumbers = list(map(int, input().strip().split()))
        if len(kktNumbers) == 0 or len(posNumbers) == 0:
            print(ERR("Вы не указали ККТ или эквайринги"))
            return
        if len(kktNumbers) != len(posNumbers):
            print(ERR("Вы указали разное количество ККТ и терминалов"))
            return
        OS.change_cashbox_service_state(True)
        kkt = []
        pos = []
        for i in range (len(kktNumbers)):
            kkt.append(KKT[kktNumbers[i]])
            pos.append(POS[posNumbers[i]])
        db = DB()
        cashboxId = db.get_cashbox_id()
        backendUrl = OS.get_backend_url_from_config(OS.find_config_path())
        le = CS().change_hardware_settings(cashboxId, kkt, pos, backendUrl)
        db.set_legalentityid_in_products(le, True)
        OS.change_cashbox_service_state(False)
        print(f"Ваши ККТ: {', '.join(kkt) }\nВаши терминалы: {', '.join(pos)}")
        SUCCESS()

class UseScanner(Command):


    @staticmethod
    def name():
        return "scanner"

    def description():
        return "Вставить марки виртуальным сканером"

    def help(message = ""):
        print(message + "\n" + f"У команды '{UseScanner.name()}' один аргумент: " 
        + "normal - выбор марки, quiet - вставка прошлой марки")
        
    def execute(*params):
        if (len(params) != 1):
            UseScanner.help(ERR("Неверное количество параметров"))
            return
        if (params[0] not in ["normal", "quiet"]):
            UseScanner.help(ERR("Неверный аргумент"))
            return
        if params[0] == "quiet":
            Mark.paste_mark_in_scanner_mode("", False, True)
        else:
            print("Какую марку вставить? Введите число: \n \n 0. Из буфера \n 1. Акцизную \n 2. Сигарет \n 3. Шин, духов, одежды, обуви, фото, воды \n 4. Молока")
            number = int(input().strip())
            if number == 0:
                Mark.paste_mark_in_scanner_mode("", True, False)
            else: 
                Mark.paste_mark_in_scanner_mode(MARKTYPES[number - 1], False, False)
        print("Код марки успешно введен в режиме сканера")
        SUCCESS()


COMMANDS = [TurnOffCashbox, SetStage, GetCashboxId, CacheCashboxId, DeleteCashbox, GenToken, 
GenGuid, SetShiftDuration, UnregLastReceipt, FlipSettings, SetHardwareSettings, UseScanner]
COMMAND_NAMES = {command.name() : command for command in COMMANDS}

def main():
    print(YO("\nКассовых успехов!\n\n"))
    print("Выберите режим: \n1. Горячие клавиши \n2. Команды в консоли")
    if (input() == "1"):
        print(YO("\nГорячие клавиши готовы!\n\n"))
        keyboard.add_hotkey("alt+5", lambda: TurnOffCashbox.execute("1"))
        keyboard.add_hotkey("alt+6", lambda: TurnOffCashbox.execute("0"))
        keyboard.add_hotkey("alt+1", lambda: SetStage.execute("1"))
        keyboard.add_hotkey("alt+2", lambda: SetStage.execute("2"))
        keyboard.add_hotkey("alt+9", lambda: SetStage.execute("9"))
        keyboard.add_hotkey("alt+i", lambda: GetCashboxId.execute())
        keyboard.add_hotkey("alt+p", lambda: CacheCashboxId.execute())
        keyboard.add_hotkey("alt+d", lambda: DeleteCashbox.execute("1", "0"))
        keyboard.add_hotkey("alt+c", lambda: DeleteCashbox.execute("0", "1"))
        keyboard.add_hotkey("alt+shift+c", lambda: DeleteCashbox.execute("1", "1"))
        keyboard.add_hotkey("alt+t", lambda: GenToken.execute())
        keyboard.add_hotkey("alt+g", lambda: GenGuid.execute())
        keyboard.add_hotkey("alt+-", lambda: SetShiftDuration.execute("24"))
        keyboard.add_hotkey("alt+e", lambda: UnregLastReceipt.execute()) 
        keyboard.add_hotkey("alt+o", lambda: FlipSettings.execute("moveRemainsToNextShift"))
        keyboard.add_hotkey("alt+a", lambda: FlipSettings.execute("prepaidEnabled"))
        keyboard.add_hotkey("alt+k", lambda: SetHardwareSettings.execute())   
        keyboard.add_hotkey('alt+s', lambda: UseScanner.execute("normal"))
        keyboard.add_hotkey('alt+shift+s', lambda: UseScanner.execute("quiet"))
        keyboard.add_abbreviation('adm1', 'https://market.testkontur.ru/AdminTools')
        keyboard.add_abbreviation('adm2', 'https://market-dev.testkontur.ru/AdminTools')
        keyboard.add_abbreviation('csadm1', 'https://market.testkontur.ru/cashboxApi/admin/web/cashbox/')
        keyboard.add_abbreviation('csadm2', 'https://market-dev.testkontur.ru/cashboxApi/admin/web/cashbox/')
        keyboard.add_abbreviation('apidoc', 'https://developer.kontur.ru/')
        keyboard.wait("alt+esc")
    else:
        print(YO("\nКонсольные команды ждут вас!\n\n"))        
        while(True):
            print("Список команд: \n")
            for command in COMMANDS:
                print("{0:>8} \t{1:<40}".format(f"{command.name()}", f"{command.description()}"))
            print("{0:>8} \t{1:<40}".format("exit", "Выйти в меню скриптов"))
            print("\n ")            
            res = input().strip().split()
            cmd = res[0]
            if cmd == "exit":
                main()
                return
            try:
                command = COMMAND_NAMES[cmd]
                command.execute(*res[1:])
            except KeyError:
                print(ERR("\nКоманда не найдена\n\n"))
if __name__ == "__main__":
    main()