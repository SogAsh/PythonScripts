import os
import datetime
import uuid
import json
from helpers import OS, CS, Mark, DB
import pyperclip
from console import fg, bg, fx
from abc import ABC, abstractmethod

KKT = ["None", "Atol", "VikiPrint", "Shtrih"]
POS = ["None", "External", "Inpas", "Ingenico", "Sberbank"]
MARKTYPES = ["Excise", "Tabak", "Cis", "Milk"]
ERR = bg.lightred + fg.black
YO = bg.green + fg.black
SUCCESS = lambda: print(YO("\nСкрипт завершился успешно\n\n"))
file_change_style = fg.lightblack + fx.italic

class Command(ABC): 
 
    @staticmethod
    @abstractmethod 
    def name(): 
        pass 
 
    @staticmethod
    @abstractmethod 
    def description(): 
        pass 
 
    @staticmethod
    @abstractmethod 
    def help(): 
        pass 
 
    @staticmethod
    @abstractmethod 
    def execute(): 
        pass
     

class TurnOffCashbox(Command):


    @staticmethod
    def name():
        return "turn"  

    @staticmethod
    def description():
        return "Отключает (1) или включает (0) службу кассы"

    @staticmethod
    def help(message = ""):
        print(message + "\n" + f"У команды '{TurnOffCashbox.name()}' один аргумент: " 
        + "1 - остановить службу, 0 - запустить")

    @staticmethod
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

    @staticmethod
    def description():
        return "Выбор стейджа для кассы: 1 или 2"

    @staticmethod
    def help(message):
        print(message + "\n" + f"У команды '{SetStage.name()}' один аргумент: " 
        + "1 - первый стейдж, 2 - второй, 9 - прод")

    @staticmethod
    def execute(*params):
        if (len(params) != 1):
            SetStage.help(ERR("Неверное количество параметров"))
            return
        if (params[0] not in ["0", "1", "9"]):
            SetStage.help(ERR("Неверный аргумент"))
            return

        stage = params[0]
        OS.change_cashbox_service_state(True)
        OS.change_staging_in_config(int(stage), OS.find_config_path())
        OS.change_cashbox_service_state(False)
        print(f"Касса готова к работе с {stage + ' стейджем' if stage != '9' else ' продом'}")
        SUCCESS() 

class GetCashboxId(Command):


    @staticmethod
    def name():
        return "getid"

    @staticmethod
    def description():
        return "Скопировать текущий cashboxId в буфер"

    @staticmethod
    def help(message = ""):
        print(message + "\n" + f"У команды '{GetCashboxId.name()}' нет аргументов:\n" 
        + "Текущий cashboxId попадает в буфер из локальной БД")

    @staticmethod
    def execute():
        cashbox_id = DB().get_cashbox_id(True)
        pyperclip.copy(cashbox_id)
        print(f"В вашем буфере обмена — текущий cashboxId: \n{cashbox_id}")
        SUCCESS()

class CacheCashboxId(Command):


    @staticmethod
    def name():
        return "setid"

    @staticmethod
    def description():
        return "Вставить cashboxId из буфера в data.json"

    @staticmethod
    def help(message = ""):
        print(message + "\n" + f"У команды '{CacheCashboxId.name()}' нет аргументов:\n" 
        + "CashboxId вставлется из буфера обмена")

    @staticmethod
    def execute():
        cashbox_id = pyperclip.paste()
        OS.cache_in_local_json("cashboxId", cashbox_id)
        print(f"Вы вставили из буфера в data.json cashboxId = \n{cashbox_id}")
        SUCCESS()

class DeleteCashbox(Command):


    @staticmethod
    def name():
        return "del"

    @staticmethod
    def description():
        return "Удалить кассу (0 1) или БД (1 0)"

    @staticmethod
    def help(message):
        print(message + "\n" + f"У команды '{DeleteCashbox.name()}' два аргумента: " 
        + "1. 1 - удалить БД, 0 - не удалять \n 2. 1 - удалить КМК, 0 - не удалять")

    @staticmethod
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
        cashbox_path = OS.find_cashbox_path()
        if delete_db:
            OS.delete_folder(os.path.join(cashbox_path, "db"))
        if delete_cashbox:
            OS.delete_folder(os.path.join(cashbox_path, "bin"))
        if delete_cashbox:
            print("Приложение кассы удалено")
        if delete_db:
            print("БД кассы удалена")
        SUCCESS()

class GenToken(Command):


    @staticmethod
    def name():
        return "token"

    @staticmethod
    def description():
        return "Сгенерировать токен для кассы"

    @staticmethod
    def help(message = ""):
        print(message + "\n" + f"У команды '{GenToken.name()}' нет аргументов:\n" 
        + "СashboxId для запроса на КС берётся из локальной базы")

    @staticmethod
    def execute():
        cashbox_id = DB().get_cashbox_id(True)
        CS().gen_token(cashbox_id)
        print(f"В вашем буфере обмена - новый токен для кассы: \n{cashbox_id}")
        SUCCESS()

class GenGuid(Command):


    @staticmethod
    def name():
        return "guid"

    @staticmethod
    def description():
        return "Сгенерировать произвольный гуид"

    @staticmethod
    def help(message = ""):
        print(message + "\n" + f"У команды '{GenGuid.name()}' нет аргументов:\n" 
        + "это нехитрая команда")

    @staticmethod
    def execute():
        guid = str(uuid.uuid4())
        pyperclip.copy(guid)
        print(f"В вашем буфере - guid: \n{guid}")
        SUCCESS()

class SetShiftDuration(Command):


    @staticmethod
    def name():
        return "shift"

    @staticmethod
    def description():
        return "Установить длительность смены в часах"

    @staticmethod
    def help(message):
        print(message + "\n" + f"У команды '{SetShiftDuration.name()}' один аргумент: " 
        + "желаемое количество часов в смене")

    @staticmethod
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

    @staticmethod
    def description():
        return "Сделать последнему чеку статус = Error"

    @staticmethod
    def help(message = ""):
        print(message + "\n" + f"У команды '{UnregLastReceipt.name()}' нет аргументов:\n" 
        + "Незарегистрированным становится последний чек")

    @staticmethod
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

    @staticmethod
    def description():
        return "Изменить буллевую настройку"

    @staticmethod
    def help(message):
        print(message + "\n" + f"У команды '{FlipSettings.name()}' один аргумент: " 
        + "название настройки. Например, moveRemainsToNextShift или prepaidEnabled")

    @staticmethod
    def execute(*params):
        if (len(params) != 1):
            FlipSettings.help(ERR("Неверное количество параметров"))
            return
        settings_name = params[0]
        cashbox_id = DB().get_cashbox_id(True)
        cs = CS()
        settings = cs.get_cashbox_settings_json(cashbox_id)
        flipped_settings = cs.flip_settings(settings, settings_name)
        cs.post_cashbox_settings(cashbox_id, flipped_settings)
        print(f'Настройка {settings_name} теперь = {settings["settings"]["backendSettings"][settings_name]}')
        SUCCESS()

class SetHardwareSettings(Command):


    @staticmethod
    def name():
        return "kkms"

    @staticmethod
    def description():
        return "Выбрать 1-2 ККТ и терминала"

    @staticmethod
    def help(message = ""):
        print(message + "\n" + f"У команды '{SetHardwareSettings.name()}' нет аргументов:\n" 
        + "Выбор техники происходит в консоли")

    @staticmethod
    def execute():
        print("""Выберите 1 или 2 ККТ: первая для ЮЛ с ИНН = 6699000000, вторая - для ЮЛ с ИНН = 992570272700
        \n0. None \n1. Atol \n2. VikiPrint\n3. Shtrih
        \nНапример, если ввели "1" - Атол в режиме 1 ЮЛ, если "2 3" - Вики и Штрих в режиме 2ЮЛ\n""")
        kkm_positions = list(map(int, input().strip().split()))
        print("""\nВыберите 1 или 2 терминала: 
        \n0. None \n1. External \n2. Inpas\n3. Ingenico \n4. Sberbank\n""")
        terminal_positions = list(map(int, input().strip().split()))
        if len(kkm_positions) == 0 or len(terminal_positions) == 0:
            print(ERR("\nВы не указали ККТ или эквайринги\n\n"))
            return
        if len(kkm_positions) != len(terminal_positions):
            print(ERR("\nВы указали разное количество ККТ и терминалов\n\n"))
            return
        OS.change_cashbox_service_state(True)
        kkms = []
        terminals = []
        for i in range (len(kkm_positions)):
            kkms.append(KKT[kkm_positions[i]])
            terminals.append(POS[terminal_positions[i]])
        db = DB()
        cashbox_id = db.get_cashbox_id()
        le = CS().change_hardware_settings(cashbox_id, kkms, terminals)
        db.set_legalentityid_in_products(le, True)
        OS.change_cashbox_service_state(False)
        print(f"Ваши ККТ: {', '.join(kkms) }\nВаши терминалы: {', '.join(terminals)}")
        SUCCESS()

class UseScanner(Command):


    @staticmethod
    def name():
        return "scanner"

    @staticmethod
    def description():
        return "Вставить марки виртуальным сканером"

    @staticmethod
    def help(message = ""):
        print(message + "\n" + f"У команды '{UseScanner.name()}' один аргумент: " 
        + "normal - выбор марки, quiet - вставка прошлой марки")

    @staticmethod       
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