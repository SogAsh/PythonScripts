import json
import sys
import subprocess
import os
import getpass

PATH = os.path.dirname(__file__)
VERSION = 4

def init():
    try: 
        requirements = os.path.join(PATH, "requirements.txt")
        subprocess.check_call([sys.executable, "-m", "ensurepip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", f"{requirements}"])
    except:
        print("\n\nНе удалось установить библиотеки.\n\nВозможно, неправильно установлен питон")
        input()
        return
    with open(os.path.join(PATH, "data.json"), "w") as file:
        file.write(fill_initial_json()) 
    print("\n\nБиблиотеки установлены, файл data.json создан успешно")
    print("Нажмите любую кнопку для продолжения...\n")
    input()

def should_init():
    json_path = os.path.join(PATH, "data.json")
    if os.path.exists(json_path):
        with open(json_path, "r") as file:
            data = json.loads(file.read())
            if "version" in data and data["version"] == VERSION:
                return False
    return True

def fill_initial_json():
    data = {}
    data["configPath"] = ""
    data["diskDrives"] = ["C:\\","D:\\","F:\\"]
    data["cashboxId"] = ""
    data["lastMark"] = "01121192496090HKMVWR6PP160TEMVENQYEJXW13PUDZUCB0TNP7LUPBG444DKNMKZCYOYMPTT1CCP7TPSLZ671W923SSWP57QFU0CCV1ZESSDYQXAFLYOGCXFPMUTXW3W5LACSDGQY6S94V3DVHH4"
    data["barcode"] = "2100000000463"
    data["version"] = VERSION
    data["secondLegalEntity"] = "617f5b99-9dd0-4e84-a0fb-35d23890de9c"
    return json.dumps(data, indent=4)

def add_to_startup():
    bat_name = "run_cashbox_scripts.bat"
    try:
        file_path = os.path.join(PATH, "main.py")
        bat_path = r'C:\Users\%s\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup' % getpass.getuser()
        if os.path.exists(os.path.join(bat_path, bat_name)):
            return 
        print("\nДобавить скрипты в автозагрузку? \n1. Да \n2. Нет\n")
        if input().strip() != "1":
            return
        with open(bat_path + '\\' + bat_name, "w+") as bat_file:
            bat_file.write(r'start "" "%s"' % file_path)
        print("\nСкрипты успешно добавлены в автозагрузку")
    except: 
        print("\n\nНе удалось добавить батник для автозапуска скриптов в папку Автозагрузка\n\n")


if (should_init()):
    init()