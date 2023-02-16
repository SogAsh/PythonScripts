import json
import sys
import subprocess
import os

PATH = os.path.dirname(__file__)

def getDataForJson():
    data = {}
    data["configPath"] = ""
    data["diskDrives"] = ["C:\\","D:\\","F:\\"]
    data["cashboxId"] = ""
    data["lastMark"] = "01121192496090HKMVWR6PP160TEMVENQYEJXW13PUDZUCB0TNP7LUPBG444DKNMKZCYOYMPTT1CCP7TPSLZ671W923SSWP57QFU0CCV1ZESSDYQXAFLYOGCXFPMUTXW3W5LACSDGQY6S94V3DVHH4"
    data["barcode"] = "2100000000463"
    return json.dumps(data, indent=4)

try: 
    requirements = os.path.join(PATH, "requirements.txt")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", f"{requirements}"])
except:
    print("\n\nНе удалось установить библиотеки.\n\nВозможно, неправильно установлен питон")
    input()

with open(os.path.join(PATH, "data.json"), "w") as file:
    data = getDataForJson()
    file.write(data) 

print("\n\nБиблиотеки установлены, файл data.json создан успешно. \nОкно можно закрыть")
input()