import os
import datetime
import uuid
from helpers.fileshelper import * 
from helpers.nethelper import *
import pyperclip
import keyboard
from console import fg, bg, fx

KKT = ["None", "Atol", "VikiPrint", "Shtrih"]
POS = ["None", "External", "Inpas", "Ingenico", "Sberbank"]
MARKTYPES = ["Excise", "Tabak", "Cis", "Milk"]
ERR = bg.lightred + fg.black
YO = bg.green + fg.black
SUCCESS = lambda: print(YO("\nСкрипт завершился успешно\n"))
file_change_style = fg.lightblack + fx.italic

class Command:
    @staticmethod
    def alias():
        raise NotImplementedError()
    def help():
        raise NotImplementedError()
    def execute(self):
        raise NotImplementedError()
    def print_result(self):
        raise NotImplementedError()	
    def name(self):
        raise NotImplementedError()
    def description(self):
        raise NotImplementedError()

class TurnOffCashbox(Command):
    @staticmethod
    def alias():
        return "turn"  
    def help(self, message = ""):
        print(message + "\n" + f"У команды '{TurnOffCashbox.alias()}' один аргумент: " 
        + "1 - остановить службу, 0 - запустить")
    def execute(self, *params):
        if (len(params) != 1):
            self.help(ERR("Неверное количество параметров"))
            return
        if (params[0] not in ["0", "1"]):
            self.help(ERR("Неверный аргумент"))
            return
        self.__should_stop = bool(int(params[0]))
        self.__success = change_cashbox_service_state(self.__should_stop)
        self.print_result()
    def print_result(self):
        if self.__success:
            print(f"Вы {'остановили' if self.__should_stop else 'запустили'} службу SKBKontur.Cashbox") 
            SUCCESS()
        else: 
            print(f"Не удалось {'остановить' if self.__should_stop else 'запустить'} службу SKBKontur.Cashbox")
    def name(self):
        return "Остановка или запуск службы"
    def description(self):
        return "Даёт команду службе кассы: stop или start"

class SetStage(Command):
    @staticmethod
    def alias():
        return "stage"
    def help(self, message):
        print(message + "\n" + f"У команды '{SetStage.alias()}' один аргумент: " 
        + "1 - первый стейдж, 2 - второй, 9 - прод")
    def execute(self, *params):
        if (len(params) != 1):
            self.help(ERR("Неверное количество параметров"))
            return
        if (params[0] not in ["0", "1", "9"]):
            self.help(ERR("Неверный аргумент"))
            return
        self.stage = params[0]
        set_staging(int(self.stage))
        self.print_result()
    def print_result(self):
        print(f"Касса готова к работе с {self.stage + ' стейджем' if self.stage != '9' else ' продом'}")
        SUCCESS() 
    def name(self):
        return "Выбор стейджа для кассы"
    def description(self):
        return """Выставляем в конфиге адрес, который соответствует первому или второму стейджу. 
            А цифре 9 соответствуют продовые настройки"""

class GetCashboxId(Command):
    @staticmethod
    def alias():
        return "getid"
    def help(self):
        return "В буфер обмена попадает текущий cashboxId - он достаётся из БД"
    def execute(self):
        self.cashboxId = get_cashbox_id()
        pyperclip.copy(self.cashboxId)
        self.print_result()
    def print_result(self):
        print(f"В вашем буфере обмена — текущий cashboxId: \n{self.cashboxId}")
        SUCCESS()
    def name(self):
        return "Получить cashboxId"

class CacheCashboxId(Command):
    @staticmethod
    def alias():
        return "setid"
    def execute(self):
        self.cashboxId = pyperclip.paste()
        cache_in_local_json("cashboxId", self.cashboxId)
        self.print_result()
    def print_result(self):
        print(f"Вы вставили из буфера в data.json cashboxId = \n{self.cashboxId}")
        SUCCESS()
    def name(self):
        return "Закэшировать CashboxId из буфера"
    def description(self):
        return """Значение из буфера окажется в файле data.json
        Это поможет сгенерировать токен, если БД пустая. 
        Если БД не пустая, команда бесполезна: все скрипты будут брать cashboxId из БД
        """

class DeleteCashbox(Command):
    @staticmethod
    def alias():
        return "del"
    def help(self, message):
        print(message + "\n" + f"У команды '{DeleteCashbox.alias()}' два аргумента: " 
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
        change_cashbox_service_state(True)
        cashboxPath = find_cashbox_path()
        if self.delete_db:
            delete_folder(os.path.join(cashboxPath, "db"))
        if self.delete_cashbox:
            delete_folder(os.path.join(cashboxPath, "bin"))
        self.print_result()
    def print_result(self):
        if self.delete_cashbox:
            print("Приложение кассы удалено")
        if self.delete_db:
            print("БД кассы удалена")
        SUCCESS()
    def name(self):
        return "Удалить кассу или БД"
    def description(self):
        return "Удалить папку с базой данных или папку bin с приложением"

class GenToken(Command):
    @staticmethod
    def alias():
        return "token"
    def execute(self):
        self.cashboxId = get_cashbox_id()
        backendUrl = get_backend_url_from_config(find_config_path())
        gen_token_CS(start_session(), self.cashboxId, backendUrl)
        self.print_result()
    def print_result(self):
        print(f"В вашем буфере обмена - новый токен для кассы: \n{self.cashboxId}")
        SUCCESS()
    def name(self):
        return "Сгенерировать токен для активации кассы"
    def description(self):
        return "Токен для активации кассы генерируется запросом к кассовому серверу"

class GenGuid(Command):
    @staticmethod
    def alias():
        return "guid"
    def execute(self):
        self.guid = str(uuid.uuid4())
        pyperclip.copy(self.guid)
        self.print_result()
    def print_result(self):
        print(f"В вашем буфере - guid: \n{self.guid}")
        SUCCESS()
    def name(self):
        return "Сгенерировать guid"
    def description(self):
        return "Генерирует произвольный гуид"

class SetShiftDuration(Command):
    @staticmethod
    def alias():
        return "shift"
    def help(self, message):
        print(message + "\n" + f"У команды '{SetShiftDuration.alias()}' один аргумент: " 
        + "желаемое количество часов в смене")
    def execute(self, *params):
        if (len(params) != 1):
            self.help(ERR("Неверное количество параметров"))
            return
        self.duration_in_hours = int(params[0])
        con = set_db_connection()
        shift = json.loads(get_last_shift_from_db(con))
        shift["openInfo"]["openDateTime"] = str(datetime.datetime.now() - datetime.timedelta(hours = self.duration_in_hours))
        edit_shift_in_db(con, json.dumps(shift), True)
        self.print_result()
    def print_result(self):
        print(f"Длительность текущей смены = {self.duration_in_hours}")
        SUCCESS()
    def name(self):
        return "Установить длительность смены"
    def description(self):
        return """Установить длительность текущей смены на КМК.
        Например, чтобы уменьшить слишком большую смену.
        Или, наоборот, посмотреть на модалы про смену больше 24 часов
        """

class UnregLastReceipt(Command):
    @staticmethod
    def alias():
        return "unreg"
    def execute(self):
        con = set_db_connection()
        (id, shiftId, number, content) = get_last_receipt(con)
        self.receipt = json.loads(content)
        self.receipt["kkmRegistrationStatus"] = "Error"
        self.receipt["correctionReceiptId"] = None
        update_receipt_content(con, json.dumps(self.receipt), id, True)
        self.print_result()
    def print_result(self):
        print(f"Последний чек продажи стал незареганным. \nОн на сумму = {self.receipt['contributedSum']}")
        SUCCESS()
    def name(self):
        return "Превращает последний чек в незарегистрированный"
    def description(self):
        return """У последнего чека в БД статус меняется на Error. 
        После этого можно провести его коррекцию"""

class FlipSettings(Command):
    @staticmethod
    def alias():
        return "settings"
    def help(self, message):
        print(message + "\n" + f"У команды '{FlipSettings.alias()}' один аргумент: " 
        + "название настройки. Например, moveRemainsToNextShift или prepaidEnabled")
    def execute(self, *params):
        if (len(params) != 1):
            self.help(ERR("Неверное количество параметров"))
            return
        self.settings_name = params[0]
        cashboxId = get_cashbox_id()
        session = start_session()
        backendUrl = get_backend_url_from_config(find_config_path())
        self.settings = get_cashbox_settings_json(session, cashboxId, backendUrl)
        flippedSettings = flip_settings_CS(self.settings, self.settings_name)
        post_cashbox_settings(session, cashboxId, flippedSettings, backendUrl)
        self.print_result()
    def print_result(self):
        print(f'Настройка {self.settings_name} теперь = {self.settings["settings"]["backendSettings"][self.settings_name]}')
        SUCCESS()
    def name(self):
        return "Изменение настройки кассы"
    def description(self):
        return """Переворачиваем значение буллевой настройки в backendSettings
        Например, moveRemainsToNextShift или prepaidEnabled
        """

class SetHardwareSettings(Command):
    @staticmethod
    def alias():
        return "kkms"
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
        change_cashbox_service_state(True)
        self.kkt = []
        self.pos = []
        for i in range (len(kktNumbers)):
            self.kkt.append(KKT[kktNumbers[i]])
            self.pos.append(POS[posNumbers[i]])
        cashboxId = get_cashbox_id()
        backendUrl = get_backend_url_from_config(find_config_path())
        le = change_hardware_settings(start_session(), cashboxId, self.kkt, self.pos, backendUrl)
        set_legalentityid_in_products(le, True)
        change_cashbox_service_state(False)
        self.print_result()
    def print_result(self):
        print(f"Ваши ККТ: {', '.join(self.kkt) }\nВаши терминалы: {', '.join(self.pos)}")
        SUCCESS()
    def name(self):
        return "Прописать в настройках ККТ и терминалы"
    def description(self):
        return """Выбранные ККТ будут прописаны в настройках на КС
        Если ККТ две - второй организации будут принадлежать товары с окончанием _2ЮЛ
        """

class UseScanner(Command):
    @staticmethod
    def alias():
        return "scanner"
    def help(self, message = ""):
        print(message + "\n" + f"У команды '{UseScanner.alias()}' один аргумент: " 
        + "normal - выбор марки, quiet - вставка прошлой марки")
    def execute(self, *params):
        if (len(params) != 1):
            self.help(ERR("Неверное количество параметров"))
            return
        if (params[0] not in ["normal", "quiet"]):
            self.help(ERR("Неверный аргумент"))
            return
        if params[0] == "quiet":
            paste_mark_in_scanner_mode("", False, True)
        else:
            print("Какую марку вставить? Введите число: \n \n 0. Из буфера \n 1. Акцизную \n 2. Сигарет \n 3. Шин, духов, одежды, обуви, фото, воды \n 4. Молока")
            number = int(input().strip())
            if number == 0:
                paste_mark_in_scanner_mode("", True, False)
            else: 
                paste_mark_in_scanner_mode(MARKTYPES[number - 1], False, False)
        self.print_result()
    def print_result(self):
        print("Код марки успешно введен в режиме сканера")
        SUCCESS()
    def name(self):
        return "Использовать виртуальный сканер"
    def description(self):
        return """В режиме сканера символы вставляются по одному (марки вставляются только так).
        Используйте сгенерированные коды марок или вставьте их из буфера
        """

COMMANDS = {
    TurnOffCashbox.alias() : TurnOffCashbox(),
    SetStage.alias() : SetStage(),
    GetCashboxId.alias() : GetCashboxId(),
    CacheCashboxId.alias() : CacheCashboxId(),
    DeleteCashbox.alias() : DeleteCashbox(),
    GenToken.alias() : GenToken(),
    GenGuid.alias() : GenGuid(),
    SetShiftDuration.alias() : SetShiftDuration(),
    UnregLastReceipt.alias() : UnregLastReceipt(),
    FlipSettings.alias() : FlipSettings(),
    SetHardwareSettings.alias() : SetHardwareSettings(),
    UseScanner.alias() : UseScanner()
}

def main():
    print(YO("\nКассовых успехов!\n\n"))
    print("Выберите режим: \n1. Горячие клавиши \n2. Команды в консоли")
    if (input() == "1"):
        keyboard.add_hotkey("alt+5", lambda: COMMANDS[TurnOffCashbox.alias()].execute("1"))
        keyboard.add_hotkey("alt+6", lambda: COMMANDS[TurnOffCashbox.alias()].execute("0"))
        keyboard.add_hotkey("alt+1", lambda: COMMANDS[SetStage.alias()].execute("1"))
        keyboard.add_hotkey("alt+2", lambda: COMMANDS[SetStage.alias()].execute("2"))
        keyboard.add_hotkey("alt+9", lambda: COMMANDS[SetStage.alias()].execute("9"))
        keyboard.add_hotkey("alt+p", lambda: COMMANDS[GetCashboxId.alias()].execute())
        keyboard.add_hotkey("alt+i", lambda: COMMANDS[CacheCashboxId.alias()].execute())
        keyboard.add_hotkey("alt+d", lambda: COMMANDS[DeleteCashbox.alias()].execute("1", "0"))
        keyboard.add_hotkey("alt+c", lambda: COMMANDS[DeleteCashbox.alias()].execute("0", "1"))
        keyboard.add_hotkey("alt+shift+c", lambda: COMMANDS[DeleteCashbox.alias()].execute("1", "1"))
        keyboard.add_hotkey("alt+t", lambda: COMMANDS[GenToken.alias()].execute())
        keyboard.add_hotkey("alt+g", lambda: COMMANDS[GenGuid.alias()].execute())
        keyboard.add_hotkey("alt+-", lambda: COMMANDS[SetShiftDuration.alias()].execute("24"))
        keyboard.add_hotkey("alt+e", lambda: COMMANDS[UnregLastReceipt.alias()].execute()) 
        keyboard.add_hotkey("alt+o", lambda: COMMANDS[FlipSettings.alias()].execute("moveRemainsToNextShift"))
        keyboard.add_hotkey("alt+a", lambda: COMMANDS[FlipSettings.alias()].execute("prepaidEnabled"))
        keyboard.add_hotkey("alt+k", lambda: COMMANDS[SetHardwareSettings.alias()].execute())   
        keyboard.add_hotkey('alt+s', lambda: COMMANDS[UseScanner.alias()].execute("normal"))
        keyboard.add_hotkey('alt+shift+s', lambda: COMMANDS[UseScanner.alias()].execute("quiet"))
        keyboard.add_abbreviation('adm1', 'https://market.testkontur.ru/AdminTools')
        keyboard.add_abbreviation('adm2', 'https://market-dev.testkontur.ru/AdminTools')
        keyboard.add_abbreviation('csadm1', 'https://market.testkontur.ru/cashboxApi/admin/web/cashbox/')
        keyboard.add_abbreviation('csadm2', 'https://market-dev.testkontur.ru/cashboxApi/admin/web/cashbox/')
        keyboard.add_abbreviation('apidoc', 'https://developer.kontur.ru/')
        keyboard.wait('alt+esc')
    else:
        print("Уже можно вводить команды \n Варианты: ")
        for command in COMMANDS:
            print(command) 
        print("\n ")
        
        while(True):
            res = input().strip().split()
            cmd = res[0]
            try:
                command = COMMANDS[cmd]
                command.execute(*res[1:])
            except KeyError:
                print("Команда не найдена")
if __name__ == "__main__":
    main()