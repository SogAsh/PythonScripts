from multiprocessing import AuthenticationError
import os
import datetime
from urllib.error import HTTPError
import uuid
import json

from requests import RequestException
import requests
from helpers import OS, CS, Mark, DB, Mode
import pyperclip
from console import fg, bg, fx
from console.utils import *
from abc import ABC, abstractmethod
import string


KKT = ["None", "Atol", "VikiPrint", "Shtrih"]
POS = ["None", "External", "Inpas", "Ingenico", "Sberbank"]
ERROR = lambda message = "При выполнении скрипта возникла ошибка": print((bg.lightred + fg.black)(f"\n{message}\n\n"))
SUCCESS = lambda message = "Скрипт завершился успешно": print((bg.green + fg.black)(f"\n{message}\n\n"))
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
    def get_expected_params():
        pass

    @staticmethod
    @abstractmethod 
    def execute(): 
        pass

    @staticmethod
    def try_execute(command, *params):
        try:
            if Command.check_params(command, *params):
                command.execute(*params)
        except requests.ConnectionError as e:
            print(e.args[0])
            ERROR("Нет связи с сервером")
        except requests.HTTPError as e:
            print(e.args[0])
            ERROR("Что-то не так с запросом")
        except Exception as e:
            print(e.args[0])
            ERROR()

    @staticmethod
    def check_params(command, *params):
        expected_params = command.get_expected_params()
        if (len(params) != len(expected_params)):
            command.help()
            ERROR("Неверное количество параметров")
            return False
        if command == SetShiftDuration:
            if not params[0].isdigit():
                command.help()
                ERROR("Неправильно указали количество часов")
                return False
            else: 
                return True
        for expected_param, param in zip(expected_params, params):
            if param not in expected_param:
                command.help()
                ERROR("Неверный аргумент")
                return False
        return True

class TurnOffCashbox(Command):


    @staticmethod
    def name():
        return "turn"  

    @staticmethod
    def description():
        return "Отключает (1) или включает (0) службу кассы"

    @staticmethod
    def help(message = ""):
        print(message + f"\nУ команды '{TurnOffCashbox.name()}' один аргумент: " 
        + "1 - остановить службу, 0 - запустить")

    @staticmethod
    def get_expected_params(): return [["0", "1"]]

    @staticmethod
    def execute(*params):
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
    def help(message = ""):
        print(message + f"\nУ команды '{SetStage.name()}' один аргумент: " 
        + "1 - первый стейдж, 2 - второй, 9 - прод")
    
    @staticmethod
    def get_expected_params(): return [["1", "2", "9"]]

    @staticmethod
    def execute(*params):
        stage = params[0]
        try:      
            OS.change_staging_in_config(int(stage), OS.find_config_path())
            print(f"Касса готова к работе с {stage + ' стейджем' if stage != '9' else ' продом'}")
            SUCCESS() 
        except Exception as e: 
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
        print(message + f"\nУ команды '{GetCashboxId.name()}' нет аргументов: " 
        + "текущий cashboxId попадает в буфер из локальной БД")

    @staticmethod
    def get_expected_params(): return []

    @staticmethod
    def execute(*params):
        try: 
            cashbox_id = DB().get_cashbox_id(True)
            pyperclip.copy(cashbox_id)
            print(f"В вашем буфере обмена — текущий cashboxId: \n{cashbox_id}")
            SUCCESS()
        except Exception as e: 
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
        print(message + f"\nУ команды '{CacheCashboxId.name()}' нет аргументов: " 
        + "сashboxId вставлется из буфера обмена")

    @staticmethod
    def get_expected_params(): return []

    @staticmethod
    def execute(*params):
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
    def help(message = ""):
        print(message + f"\nУ команды '{DeleteCashbox.name()}' два аргумента: \n" 
        + "1. 1 - удалить БД, 0 - не удалять \n 2. 1 - удалить КМК, 0 - не удалять")

    @staticmethod
    def get_expected_params(): return [["0", "1"], ["0", "1"]]

    @staticmethod
    def execute(*params):
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
            print("Не удалось удалить папку")
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
        print(message + f"\nУ команды '{GenToken.name()}' нет аргументов: " 
        + "cashboxId для запроса на КС берётся из локальной базы")

    @staticmethod
    def get_expected_params(): return []

    @staticmethod
    def execute(*params):
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
        print(message + f"\nУ команды '{GenGuid.name()}' нет аргументов")

    @staticmethod
    def get_expected_params(): return []

    @staticmethod
    def execute(*params):
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
    def help(message = ""):
        print(message + f"\nУ команды '{SetShiftDuration.name()}' один аргумент: " 
        + "желаемое количество часов в смене")

    @staticmethod
    def get_expected_params(): return [list()]

    @staticmethod
    def execute(*params):
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
        print(message + f"\nУ команды '{UnregLastReceipt.name()}' нет аргументов: " 
        + "незарегистрированным становится последний чек")

    @staticmethod
    def get_expected_params(): return []

    @staticmethod
    def execute(*params):
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
    def help(message = ""):
        print(message + f"\nУ команды '{FlipSettings.name()}' один аргумент: " 
        + "название настройки. Например, moveRemainsToNextShift или prepaidEnabled")

    @staticmethod
    def get_expected_params(): return [["moveRemainsToNextShift", "prepaidEnabled"]]

    @staticmethod
    def execute(*params):
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
        print(message + f"\nУ команды '{SetHardwareSettings.name()}' нет аргументов: " 
        + "выбор техники происходит в консоли")

    @staticmethod
    def get_expected_params(): return []

    @staticmethod
    def execute(*params):
        print("""Выберите 1 или 2 ККТ: первая для ЮЛ с ИНН = 6699000000, вторая - для ЮЛ с ИНН = 992570272700
        \n0. None \n1. Atol \n2. VikiPrint\n3. Shtrih
        \nНапример, если ввели "1" - Атол в режиме 1 ЮЛ, если "2 3" - Вики и Штрих в режиме 2ЮЛ\n""")
        try: 
            kkm_positions = list(map(int, input().strip().split()))
            print("""\nВыберите 1 или 2 терминала: 
            \n0. None \n1. External \n2. Inpas\n3. Ingenico \n4. Sberbank\n""")
            terminal_positions = list(map(int, input().strip().split()))
        except(ValueError):
            ERROR("Вместо цифр ввели какие-то буквы")
            return
        if len(kkm_positions) == 0 or len(terminal_positions) == 0:
            ERROR("Вы не указали ККТ или эквайринги")
            return
        if len(kkm_positions) != len(terminal_positions):
            ERROR("Вы указали разное количество ККТ и терминалов")
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
        print(message + f"\nУ команды '{UseScanner.name()}' один аргумент: " 
        + "normal - выбор марки, quiet - вставка прошлой марки")

    @staticmethod
    def get_expected_params(): return [["normal", "quiet"]]

    @staticmethod       
    def execute(*params):
        if params[0] == "quiet":
            Mark.paste_mark_in_scanner_mode("", Mode.QUIET)
        else:
            print("Какую марку вставить? Введите число:\n")
            print("0. Из буфера")
            Mark.print_marktypes()
            number = input().strip()
            if number not in string.digits:
                ERROR("Вы ввели не число")
                return
            number = int(number)
            if number > len(Mark.MARKTYPES):
                ERROR("Неверное число")
                return
            if number == 0:
                Mark.paste_mark_in_scanner_mode("", Mode.CLIPBOARD)
            else: 
                Mark.paste_mark_in_scanner_mode(Mark.MARKTYPES[number - 1][0], Mode.NORMAL)
        print("Код марки успешно введен в режиме сканера")
        SUCCESS()