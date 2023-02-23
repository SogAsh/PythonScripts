import os
import datetime
import uuid
import json
from helpers import OS, CS, Mark, DB, Mode
import pyperclip
from console import fg, bg, fx
from abc import ABC, abstractmethod
import string

KKT = ["None", "Atol", "VikiPrint", "Shtrih"]
POS = ["None", "External", "Inpas", "Ingenico", "Sberbank"]
ERROR_FORMAT = bg.lightred + fg.black
SUCCESS_FORMAT = bg.green + fg.black
ERROR = lambda: print(ERROR_FORMAT("\nПри выполнении скрипта возникла ошибка\n\n"))
SUCCESS = lambda: print(SUCCESS_FORMAT("\nСкрипт завершился успешно\n\n"))
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
            TurnOffCashbox.help(ERROR_FORMAT("Неверное количество параметров"))
            return
        if (params[0] not in ["0", "1"]):
            TurnOffCashbox.help(ERROR_FORMAT("Неверный аргумент"))
            return
        should_stop = bool(int(params[0]))
        try:
            OS.change_cashbox_service_state(should_stop)
            print(f"\nВы {'остановили' if should_stop else 'запустили'} службу SKBKontur.Cashbox") 
            SUCCESS()
        except:
            print(f"\nНе удалось {'остановить' if should_stop else 'запустить'} службу SKBKontur.Cashbox")
            ERROR()


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
            SetStage.help(ERROR_FORMAT("Неверное количество параметров"))
            return
        if (params[0] not in ["0", "1", "9"]):
            SetStage.help(ERROR_FORMAT("Неверный аргумент"))
            return

        stage = params[0]
        try:      
            OS.change_staging_in_config(int(stage), OS.find_config_path())
            print(f"Касса готова к работе с {stage + ' стейджем' if stage != '9' else ' продом'}")
            SUCCESS() 
        except: 
            print(f"Не удалось переключить стейдж. Проверьте, в каком состоянии служба кассы")
            ERROR()
            

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
        try: 
            cashbox_id = DB().get_cashbox_id(True)
            pyperclip.copy(cashbox_id)
            print(f"В вашем буфере обмена — текущий cashboxId: \n{cashbox_id}")
            SUCCESS()
        except: 
            print("Не удалось получить из базы CashboxId")
            ERROR()


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
            DeleteCashbox.help(ERROR_FORMAT("Неверное количество параметров"))
            return
        if (params[0] not in ["0", "1"] or params[1] not in ["0", "1"]):
            DeleteCashbox.help(ERROR_FORMAT("Неверный аргумент"))
            return
        delete_db = bool(int(params[0]))
        delete_cashbox = bool(int(params[1]))
        OS.change_cashbox_service_state(True)
        cashbox_path = OS.find_cashbox_path()
        try:
            if delete_db:
                OS.delete_folder(os.path.join(cashbox_path, "db"))
                print("БД кассы удалена")
            if delete_cashbox:
                OS.delete_folder(os.path.join(cashbox_path, "bin"))
                print("Приложение кассы удалено")
            SUCCESS()
        except:
            ERROR()


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
        try:
            cashbox_id = DB().get_cashbox_id(True)
            CS().gen_token(cashbox_id)
            print(f"В вашем буфере обмена - новый токен для кассы: \n{cashbox_id}")
            SUCCESS()
        except:
            print("Не удалось сгенерировать токен. Возможно, не подключен VPN Контура")
            ERROR()

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
            SetShiftDuration.help(ERROR_FORMAT("Неверное количество параметров"))
            return
        try:
            duration_in_hours = int(params[0])
            db = DB()
            shift = json.loads(db.get_last_shift_from_db())
            shift["openInfo"]["openDateTime"] = str(datetime.datetime.now() - datetime.timedelta(hours = duration_in_hours))
            db.edit_shift_in_db(json.dumps(shift), True)
            print(f"Длительность текущей смены = {duration_in_hours}")
            SUCCESS()
        except:
            print("Не удалось изменить смену в БД")
            ERROR()

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
        try:
            db = DB()
            (id, shiftId, number, content) = db.get_last_receipt()
            receipt = json.loads(content)
            receipt["kkmRegistrationStatus"] = "Error"
            receipt["correctionReceiptId"] = None
            db.update_receipt_content(json.dumps(receipt), id, True)
            print(f"Последний чек продажи стал незареганным. \nОн на сумму = {receipt['contributedSum']}")
            SUCCESS()
        except: 
            print("Не удалось изменить чек в БД")
            ERROR()

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
            FlipSettings.help(ERROR_FORMAT("Неверное количество параметров"))
            return
        try:
            settings_name = params[0]
            cashbox_id = DB().get_cashbox_id(True)
            cs = CS()
            settings = cs.get_cashbox_settings_json(cashbox_id)
            flipped_settings = cs.flip_settings(settings, settings_name)
            cs.post_cashbox_settings(cashbox_id, flipped_settings)
            print(f'Настройка {settings_name} теперь = {settings["settings"]["backendSettings"][settings_name]}')
            SUCCESS()
        except: 
            print("Не удалось изменить настройки. Возможно, не подключен VPN Контура")
            ERROR()

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
        try: 
            kkm_positions = list(map(int, input().strip().split()))
            print("""\nВыберите 1 или 2 терминала: 
            \n0. None \n1. External \n2. Inpas\n3. Ingenico \n4. Sberbank\n""")
            terminal_positions = list(map(int, input().strip().split()))
        except(ValueError):
            print(ERROR_FORMAT("Вместо цифр ввели какие-то буквы"))
            return
        if len(kkm_positions) == 0 or len(terminal_positions) == 0:
            print(ERROR_FORMAT("\nВы не указали ККТ или эквайринги\n\n"))
            return
        if len(kkm_positions) != len(terminal_positions):
            print(ERROR_FORMAT("\nВы указали разное количество ККТ и терминалов\n\n"))
            return
        try: 
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
        except:
            print("Не удалось установить настройки оборудования. Возможно, не подключен VPN Контура")
            ERROR()

class UseScanner(Command):


    @staticmethod
    def name():
        return "scanner"

    @staticmethod
    def description():
        return "Вставить марки виртуальным сканером"

    @staticmethod
    def help(message = ""):
        print(message + f"\n\nУ команды '{UseScanner.name()}' один аргумент: " 
        + "normal - выбор марки, quiet - вставка прошлой марки")

    @staticmethod       
    def execute(*params):
        if (len(params) != 1):
            UseScanner.help(ERROR_FORMAT("\nНеверное количество параметров"))
            return
        if (params[0] not in ["normal", "quiet"]):
            UseScanner.help(ERROR_FORMAT("\nНеверный аргумент"))
            return
        if params[0] == "quiet":
            Mark.paste_mark_in_scanner_mode("", Mode.QUIET)
        else:
            print("Какую марку вставить? Введите число:\n")
            print("0. Из буфера")
            Mark.print_marktypes()
            number = input().strip()
            if number not in string.digits:
                print(ERROR_FORMAT("\nВы ввели не число\n\n"))
                return
            number = int(number)
            if number > len(Mark.MARKTYPES):
                print(ERROR_FORMAT("\nНеверное число\n\n"))
                return
            if number == 0:
                Mark.paste_mark_in_scanner_mode("", Mode.CLIPBOARD)
            else: 
                Mark.paste_mark_in_scanner_mode(Mark.MARKTYPES[number - 1][0], Mode.NORMAL)
        print("Код марки успешно введен в режиме сканера")
        SUCCESS()