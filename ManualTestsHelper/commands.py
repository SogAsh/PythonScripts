import os
import datetime
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
    def description(self):
        raise NotImplementedError()
    def help():
        raise NotImplementedError()
    def execute(self):
        raise NotImplementedError()
    def print_result(self):
        raise NotImplementedError()	

class TurnOffCashbox(Command):
    @staticmethod
    def name():
        return "turn"  
    def description(self):
        return "Даёт команду службе кассы: stop или start"
    def help(self, message = ""):
        print(message + "\n" + f"У команды '{TurnOffCashbox.name()}' один аргумент: " 
        + "1 - остановить службу, 0 - запустить")
    def execute(self, *params):
        if (len(params) != 1):
            self.help(ERR("Неверное количество параметров"))
            return
        if (params[0] not in ["0", "1"]):
            self.help(ERR("Неверный аргумент"))
            return
        self.__should_stop = bool(int(params[0]))
        self.__success = OS.change_cashbox_service_state(self.__should_stop)
        self.print_result()
    def print_result(self):
        if self.__success:
            print(f"Вы {'остановили' if self.__should_stop else 'запустили'} службу SKBKontur.Cashbox") 
            SUCCESS()
        else: 
            print(f"Не удалось {'остановить' if self.__should_stop else 'запустить'} службу SKBKontur.Cashbox")

class SetStage(Command):
    @staticmethod
    def name():
        return "stage"
    def description(self):
        return "Выбор стейджа для кассы"
    def help(self, message):
        print(message + "\n" + f"У команды '{SetStage.name()}' один аргумент: " 
        + "1 - первый стейдж, 2 - второй, 9 - прод")
    def execute(self, *params):
        if (len(params) != 1):
            self.help(ERR("Неверное количество параметров"))
            return
        if (params[0] not in ["0", "1", "9"]):
            self.help(ERR("Неверный аргумент"))
            return
        self.stage = params[0]
        OS.set_staging(int(self.stage))
        self.print_result()
    def print_result(self):
        print(f"Касса готова к работе с {self.stage + ' стейджем' if self.stage != '9' else ' продом'}")
        SUCCESS() 

class GetCashboxId(Command):
    @staticmethod
    def name():
        return "getid"
    def help(self):
        return "В буфер обмена попадает текущий cashboxId - он достаётся из БД"
    def execute(self):
        self.cashboxId = DB().get_cashbox_id()
        pyperclip.copy(self.cashboxId)
        self.print_result()
    def print_result(self):
        print(f"В вашем буфере обмена — текущий cashboxId: \n{self.cashboxId}")
        SUCCESS()
    def description(self):
        return "Получить cashboxId в буфер обмена"

class CacheCashboxId(Command):
    @staticmethod
    def name():
        return "setid"
    def description(self):
        return "Вставить CashboxId из буфера в data.json"
    def execute(self):
        self.cashboxId = pyperclip.paste()
        OS.cache_in_local_json("cashboxId", self.cashboxId)
        self.print_result()
    def print_result(self):
        print(f"Вы вставили из буфера в data.json cashboxId = \n{self.cashboxId}")
        SUCCESS()

class DeleteCashbox(Command):
    @staticmethod
    def name():
        return "del"
    def description(self):
        return "Удалить кассу или БД"
    def help(self, message):
        print(message + "\n" + f"У команды '{DeleteCashbox.name()}' два аргумента: " 
        + "1. 1 - удалить БД, 0 - не удалять \n 2. 1 - удалить КМК, 0 - не удалять")
    def execute(self, *params):
        if (len(params) != 2):
            self.help(ERR("Неверное количество параметров"))
            return
        if (params[0] not in ["0", "1"] or params[1] not in ["0", "1"]):
            self.help(ERR("Неверный аргумент"))
            return
        self.delete_db = bool(int(params[0]))
        self.delete_cashbox = bool(int(params[1]))
        OS.change_cashbox_service_state(True)
        cashboxPath = OS.find_cashbox_path()
        if self.delete_db:
            OS.delete_folder(os.path.join(cashboxPath, "db"))
        if self.delete_cashbox:
            OS.delete_folder(os.path.join(cashboxPath, "bin"))
        self.print_result()
    def print_result(self):
        if self.delete_cashbox:
            print("Приложение кассы удалено")
        if self.delete_db:
            print("БД кассы удалена")
        SUCCESS()

class GenToken(Command):
    @staticmethod
    def name():
        return "token"
    def description(self):
        return "Сгенерировать токен для активации кассы"
    def execute(self):
        self.cashboxId = DB().get_cashbox_id()
        backendUrl = OS.get_backend_url_from_config(OS.find_config_path())
        cs = CS()
        cs.gen_token_CS(cs.start_session(), self.cashboxId, backendUrl)
        self.print_result()
    def print_result(self):
        print(f"В вашем буфере обмена - новый токен для кассы: \n{self.cashboxId}")
        SUCCESS()

class GenGuid(Command):
    @staticmethod
    def name():
        return "guid"
    def description(self):
        return "Сгенерировать произвольный гуид"
    def execute(self):
        self.guid = str(uuid.uuid4())
        pyperclip.copy(self.guid)
        self.print_result()
    def print_result(self):
        print(f"В вашем буфере - guid: \n{self.guid}")
        SUCCESS()

class SetShiftDuration(Command):
    @staticmethod
    def name():
        return "shift"
    def description(self):
        return "Установить длительность смены на КМК"
    def help(self, message):
        print(message + "\n" + f"У команды '{SetShiftDuration.name()}' один аргумент: " 
        + "желаемое количество часов в смене")
    def execute(self, *params):
        if (len(params) != 1):
            self.help(ERR("Неверное количество параметров"))
            return
        self.duration_in_hours = int(params[0])
        db = DB()
        con = db.set_db_connection()
        shift = json.loads(db.get_last_shift_from_db(con))
        shift["openInfo"]["openDateTime"] = str(datetime.datetime.now() - datetime.timedelta(hours = self.duration_in_hours))
        db.edit_shift_in_db(con, json.dumps(shift), True)
        self.print_result()
    def print_result(self):
        print(f"Длительность текущей смены = {self.duration_in_hours}")
        SUCCESS()

class UnregLastReceipt(Command):
    @staticmethod
    def name():
        return "unreg"
    def description(self):
        return "Делает статус последнего чека в БД = Error"
    def execute(self):
        db = DB()
        con = db.set_db_connection()
        (id, shiftId, number, content) = db.get_last_receipt(con)
        self.receipt = json.loads(content)
        self.receipt["kkmRegistrationStatus"] = "Error"
        self.receipt["correctionReceiptId"] = None
        db.update_receipt_content(con, json.dumps(self.receipt), id, True)
        self.print_result()
    def print_result(self):
        print(f"Последний чек продажи стал незареганным. \nОн на сумму = {self.receipt['contributedSum']}")
        SUCCESS()

class FlipSettings(Command):
    @staticmethod
    def name():
        return "settings"
    def description(self):
        return "Изменение буллевых настроек кассы"
    def help(self, message):
        print(message + "\n" + f"У команды '{FlipSettings.name()}' один аргумент: " 
        + "название настройки. Например, moveRemainsToNextShift или prepaidEnabled")
    def execute(self, *params):
        if (len(params) != 1):
            self.help(ERR("Неверное количество параметров"))
            return
        self.settings_name = params[0]
        cashboxId = DB().get_cashbox_id()
        cs = CS()
        session = cs.start_session()
        backendUrl = OS.get_backend_url_from_config(OS.find_config_path())
        self.settings = cs.get_cashbox_settings_json(session, cashboxId, backendUrl)
        flippedSettings = cs.flip_settings_CS(self.settings, self.settings_name)
        cs.post_cashbox_settings(session, cashboxId, flippedSettings, backendUrl)
        self.print_result()
    def print_result(self):
        print(f'Настройка {self.settings_name} теперь = {self.settings["settings"]["backendSettings"][self.settings_name]}')
        SUCCESS()

class SetHardwareSettings(Command):
    @staticmethod
    def name():
        return "kkms"
    def description(self):
        return "Выбрать 1-2 ККТ и терминала"
    def execute(self):
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
        self.kkt = []
        self.pos = []
        for i in range (len(kktNumbers)):
            self.kkt.append(KKT[kktNumbers[i]])
            self.pos.append(POS[posNumbers[i]])
        db = DB()
        cashboxId = db.get_cashbox_id()
        backendUrl = OS.get_backend_url_from_config(OS.find_config_path())
        cs = CS()
        le = cs.change_hardware_settings(cs.start_session(), cashboxId, self.kkt, self.pos, backendUrl)
        db.set_legalentityid_in_products(le, True)
        OS.change_cashbox_service_state(False)
        self.print_result()
    def print_result(self):
        print(f"Ваши ККТ: {', '.join(self.kkt) }\nВаши терминалы: {', '.join(self.pos)}")
        SUCCESS()

class UseScanner(Command):
    @staticmethod
    def name():
        return "scanner"
    def description(self):
        return "Вставить марки виртуальным сканером"
    def help(self, message = ""):
        print(message + "\n" + f"У команды '{UseScanner.name()}' один аргумент: " 
        + "normal - выбор марки, quiet - вставка прошлой марки")
    def execute(self, *params):
        if (len(params) != 1):
            self.help(ERR("Неверное количество параметров"))
            return
        if (params[0] not in ["normal", "quiet"]):
            self.help(ERR("Неверный аргумент"))
            return
        mark = Mark()
        if params[0] == "quiet":
            mark.paste_mark_in_scanner_mode("", False, True)
        else:
            print("Какую марку вставить? Введите число: \n \n 0. Из буфера \n 1. Акцизную \n 2. Сигарет \n 3. Шин, духов, одежды, обуви, фото, воды \n 4. Молока")
            number = int(input().strip())
            if number == 0:
                mark.paste_mark_in_scanner_mode("", True, False)
            else: 
                mark.paste_mark_in_scanner_mode(MARKTYPES[number - 1], False, False)
        self.print_result()
    def print_result(self):
        print("Код марки успешно введен в режиме сканера")
        SUCCESS()


COMMANDS = [TurnOffCashbox(), SetStage(), GetCashboxId(), CacheCashboxId(), DeleteCashbox(), GenToken(), 
GenGuid(), SetShiftDuration(), UnregLastReceipt(), FlipSettings(), SetHardwareSettings(), UseScanner()]
COMMAND_NAMES = {command.name() : command for command in COMMANDS}
COMMAND_DESCRIPTIONS = {command.name() : command.description() for command in COMMANDS}

def main():
    print(YO("\nКассовых успехов!\n\n"))
    print("Выберите режим: \n1. Горячие клавиши \n2. Команды в консоли")
    if (input() == "1"):
        keyboard.add_hotkey("alt+5", lambda: COMMAND_NAMES[TurnOffCashbox.name()].execute("1"))
        keyboard.add_hotkey("alt+6", lambda: COMMAND_NAMES[TurnOffCashbox.name()].execute("0"))
        keyboard.add_hotkey("alt+1", lambda: COMMAND_NAMES[SetStage.name()].execute("1"))
        keyboard.add_hotkey("alt+2", lambda: COMMAND_NAMES[SetStage.name()].execute("2"))
        keyboard.add_hotkey("alt+9", lambda: COMMAND_NAMES[SetStage.name()].execute("9"))
        keyboard.add_hotkey("alt+p", lambda: COMMAND_NAMES[GetCashboxId.name()].execute())
        keyboard.add_hotkey("alt+i", lambda: COMMAND_NAMES[CacheCashboxId.name()].execute())
        keyboard.add_hotkey("alt+d", lambda: COMMAND_NAMES[DeleteCashbox.name()].execute("1", "0"))
        keyboard.add_hotkey("alt+c", lambda: COMMAND_NAMES[DeleteCashbox.name()].execute("0", "1"))
        keyboard.add_hotkey("alt+shift+c", lambda: COMMAND_NAMES[DeleteCashbox.name()].execute("1", "1"))
        keyboard.add_hotkey("alt+t", lambda: COMMAND_NAMES[GenToken.name()].execute())
        keyboard.add_hotkey("alt+g", lambda: COMMAND_NAMES[GenGuid.name()].execute())
        keyboard.add_hotkey("alt+-", lambda: COMMAND_NAMES[SetShiftDuration.name()].execute("24"))
        keyboard.add_hotkey("alt+e", lambda: COMMAND_NAMES[UnregLastReceipt.name()].execute()) 
        keyboard.add_hotkey("alt+o", lambda: COMMAND_NAMES[FlipSettings.name()].execute("moveRemainsToNextShift"))
        keyboard.add_hotkey("alt+a", lambda: COMMAND_NAMES[FlipSettings.name()].execute("prepaidEnabled"))
        keyboard.add_hotkey("alt+k", lambda: COMMAND_NAMES[SetHardwareSettings.name()].execute())   
        keyboard.add_hotkey('alt+s', lambda: COMMAND_NAMES[UseScanner.name()].execute("normal"))
        keyboard.add_hotkey('alt+shift+s', lambda: COMMAND_NAMES[UseScanner.name()].execute("quiet"))
        keyboard.add_abbreviation('adm1', 'https://market.testkontur.ru/AdminTools')
        keyboard.add_abbreviation('adm2', 'https://market-dev.testkontur.ru/AdminTools')
        keyboard.add_abbreviation('csadm1', 'https://market.testkontur.ru/cashboxApi/admin/web/cashbox/')
        keyboard.add_abbreviation('csadm2', 'https://market-dev.testkontur.ru/cashboxApi/admin/web/cashbox/')
        keyboard.add_abbreviation('apidoc', 'https://developer.kontur.ru/')
        keyboard.wait('alt+esc')
    else:
        print("Уже можно вводить команды \n")        
        while(True):
            print("Список команд: \n")
            # здесь выводить команду с description в две колонки
            for command in COMMAND_NAMES:
                print(command) 
            print("\n ")            
            res = input().strip().split()
            cmd = res[0]
            try:
                command = COMMAND_NAMES[cmd]
                command.execute(*res[1:])
            except KeyError:
                print("Команда не найдена")
if __name__ == "__main__":
    main()