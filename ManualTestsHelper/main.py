import ctypes
import sys
if not ctypes.windll.shell32.IsUserAnAdmin(): 
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)        
    exit() 
from ini import *
import keyboard
from commands import *
import win32api
import time
import subprocess

COMMANDS = [TurnOffCashbox, SetStage, GetCashboxId, CacheCashboxId, DeleteCashbox, GenToken, 
GenGuid, SetShiftDuration, UnregLastReceipt, FlipSettings, SetHardwareSettings, UseScanner]

COMMAND_NAMES = {command.name() : command for command in COMMANDS}

HOTKEYS = [
    ("alt+5", TurnOffCashbox, ["1"]),
    ("alt+6", TurnOffCashbox, ["0"]),
    ("alt+1", SetStage, ["1"]), 
    ("alt+2", SetStage, ["2"]), 
    ("alt+9", SetStage, ["9"]), 
    ("alt+i", GetCashboxId, []),
    ("alt+p", CacheCashboxId, []),
    ("alt+d", DeleteCashbox, ["1", "0"]),
    ("alt+c", DeleteCashbox, ["0", "1"]),
    ("alt+shift+c", DeleteCashbox, ["1", "1"]),
    ("alt+t", GenToken, []),
    ("alt+g", GenGuid, []),
    ("alt+-", SetShiftDuration, ["24"]),
    ("alt+e", UnregLastReceipt, []),
    ("alt+o", FlipSettings, ["moveRemainsToNextShift"]),
    ("alt+a", FlipSettings, ["prepaidEnabled"]),
    ("alt+k", SetHardwareSettings, []),
    ("alt+s", UseScanner, ["normal"]),
    ("alt+shift+s", UseScanner, ["quiet"])
]

HOTKEY_NAMES = [(a, b.description(), " ".join(c)) for a, b, c in HOTKEYS]

HOTSTRINGS = [
    ("adm1", "Админка Маркета-1", "https://market.testkontur.ru/AdminTools"),
    ("adm2", "Админка Маркета-2", "https://market-dev.testkontur.ru/AdminTools"),
    ("csadm1", "Админка КС-1", "https://market.testkontur.ru/cashboxApi/admin/web/cashbox/"),
    ("csadm2", "Админка КС-2", "https://market-dev.testkontur.ru/cashboxApi/admin/web/cashbox/"),
    ("apidoc", "Документация", "https://developer.kontur.ru/")
]

def main():
    print(SUCCESS_FORMAT("\nКассовых успехов!\n\n"))
    print("Выберите режим: \n1. Горячие клавиши \n2. Команды в консоли")
    if (input() == "1"):
        print(SUCCESS_FORMAT("\nГорячие клавиши готовы!\n\n"))
        for key, command, params in HOTKEYS:
            add_hotkey(key, command, params)
        for key, _, value in HOTSTRINGS:
            add_hotstring(key, value)
        keyboard.add_hotkey("alt+h", lambda: print_hotkeys())
        print_hotkeys()
        restartAfterLocking()    
    else:
        print(SUCCESS_FORMAT("\nКонсольные команды ждут вас!\n\n"))        
        while(True):
            print_commands()
            res = input().strip().split()
            cmd = res[0]
            if cmd == "exit":
                main()
                return
            try:
                command = COMMAND_NAMES[cmd]
                command.execute(*res[1:])
            except KeyError:
                print(ERROR_FORMAT("\nКоманда не найдена\n\n"))

def add_hotkey(key, command, params):
    keyboard.add_hotkey(key, lambda: command.execute(*params))

def add_hotstring(abbrev, phrase):
    keyboard.add_abbreviation(abbrev, phrase)

def print_hotkeys():
    format = "{0:<8} \t{1:<40} \t{2:20}"
    print(format.format("Комбо", "Описание команды", "Аргументы"))
    for key, description, args in HOTKEY_NAMES:
        print(format.format(key, description, args))
    print(format.format(f"alt+h", f"Вывести список горячих клавиш в консоль", ""))
    print_hotstrings()

def print_hotstrings():
    format = "{0:<15} \t{1:<7} \t{2:40}"
    print("\n\nА для автозамены введите ключ куда угодно и поставьте пробел:\n")
    print(format.format("Что это","Ключ", "Результат замены"))
    for key, description, value in HOTSTRINGS:
        print(format.format(description, key, value))
    print("\n")

def print_commands():
    format = "{0:<8} \t{1:<40}"
    print(format.format("Команда", "Описание"))
    for command in COMMANDS:
        print(format.format(f"{command.name()}", f"{command.description()}"))
    print(format.format("exit", "Выйти в меню скриптов"))
    print("\n ") 

def isScreenLocked():
    process_name='LogonUI.exe'
    outputall=subprocess.check_output('TASKLIST')
    if process_name in str(outputall):
        return True
    return False

def restartAfterLocking():
    while not isScreenLocked():
            time.sleep(5)
    while(True):
        time.sleep(1)
        if not isScreenLocked():
            print("Перезапуск после блокировки...\n")
            os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)

if __name__ == "__main__":
    add_to_startup()
    win32api.LoadKeyboardLayout('00000409',1)
    main()