import ctypes
from ini import *
import keyboard
from commands import *

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

HOTSTRINGS = {
    "adm1" : "https://market.testkontur.ru/AdminTools",
    "adm2" : "https://market-dev.testkontur.ru/AdminTools",
    "csadm1" : "https://market.testkontur.ru/cashboxApi/admin/web/cashbox/",
    "csadm2" : "https://market-dev.testkontur.ru/cashboxApi/admin/web/cashbox/",
    "apidoc" : "https://developer.kontur.ru/"
}

def add_hotkey(key, command, params):
    keyboard.add_hotkey(key, lambda: command.execute(*params))

def add_hotstring(abbrev, phrase):
    keyboard.add_abbreviation(abbrev, phrase)

def main():
    print(YO("\nКассовых успехов!\n\n"))
    print("Выберите режим: \n1. Горячие клавиши \n2. Команды в консоли")
    if (input() == "1"):
        print(YO("\nГорячие клавиши готовы!\n\n"))
        for key, command, params in HOTKEYS:
            add_hotkey(key, command, params)
        for abbrev, phrase in HOTSTRINGS.items():
            add_hotstring(abbrev, phrase)
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
    if not ctypes.windll.shell32.IsUserAnAdmin(): 
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)        
        exit() 
    if (should_init()):
        init()
    main()