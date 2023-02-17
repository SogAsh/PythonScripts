import json
import sys
import subprocess
import os

PATH = os.path.dirname(__file__)

def init():
    try: 
        requirements = os.path.join(PATH, "requirements.txt")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", f"{requirements}"])
    except:
        print("\n\nНе удалось установить библиотеки.\n\nВозможно, неправильно установлен питон")
        input()
        return
    with open(os.path.join(PATH, "data.json"), "w") as file:
        file.write(fill_initial_json()) 
    print("\n\nБиблиотеки установлены, файл data.json создан успешно")
    print("Нажмите любую кнопку для продолжения")
    input()

def should_init():
    json_path = os.path.join(PATH, "data.json")
    if os.path.exists(json_path):
        with open(json_path, "r") as file:
            data = json.loads(file.read())
            if "initialized" in data and data["initialized"] == "True":
                return False
    return True

def fill_initial_json():
    data = {}
    data["configPath"] = ""
    data["diskDrives"] = ["C:\\","D:\\","F:\\"]
    data["cashboxId"] = ""
    data["lastMark"] = "01121192496090HKMVWR6PP160TEMVENQYEJXW13PUDZUCB0TNP7LUPBG444DKNMKZCYOYMPTT1CCP7TPSLZ671W923SSWP57QFU0CCV1ZESSDYQXAFLYOGCXFPMUTXW3W5LACSDGQY6S94V3DVHH4"
    data["barcode"] = "2100000000463"
    data["initialized"] = "True"
    return json.dumps(data, indent=4)

if (should_init()):
    init()