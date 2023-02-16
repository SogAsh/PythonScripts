import keyboard
from console import fg, bg, fx
from commands import *

COMMANDS = [TurnOffCashbox, SetStage, GetCashboxId, CacheCashboxId, DeleteCashbox, GenToken, 
GenGuid, SetShiftDuration, UnregLastReceipt, FlipSettings, SetHardwareSettings, UseScanner]
COMMAND_NAMES = {command.name() : command for command in COMMANDS}

def main():
    print(YO("\nКассовых успехов!\n\n"))
    print("Выберите режим: \n1. Горячие клавиши \n2. Команды в консоли")
    if (input() == "1"):
        print(YO("\nГорячие клавиши готовы!\n\n"))
        keyboard.add_hotkey("alt+5", lambda: TurnOffCashbox.execute("1"))
        keyboard.add_hotkey("alt+6", lambda: TurnOffCashbox.execute("0"))
        keyboard.add_hotkey("alt+1", lambda: SetStage.execute("1"))
        keyboard.add_hotkey("alt+2", lambda: SetStage.execute("2"))
        keyboard.add_hotkey("alt+9", lambda: SetStage.execute("9"))
        keyboard.add_hotkey("alt+i", lambda: GetCashboxId.execute())
        keyboard.add_hotkey("alt+p", lambda: CacheCashboxId.execute())
        keyboard.add_hotkey("alt+d", lambda: DeleteCashbox.execute("1", "0"))
        keyboard.add_hotkey("alt+c", lambda: DeleteCashbox.execute("0", "1"))
        keyboard.add_hotkey("alt+shift+c", lambda: DeleteCashbox.execute("1", "1"))
        keyboard.add_hotkey("alt+t", lambda: GenToken.execute())
        keyboard.add_hotkey("alt+g", lambda: GenGuid.execute())
        keyboard.add_hotkey("alt+-", lambda: SetShiftDuration.execute("24"))
        keyboard.add_hotkey("alt+e", lambda: UnregLastReceipt.execute()) 
        keyboard.add_hotkey("alt+o", lambda: FlipSettings.execute("moveRemainsToNextShift"))
        keyboard.add_hotkey("alt+a", lambda: FlipSettings.execute("prepaidEnabled"))
        keyboard.add_hotkey("alt+k", lambda: SetHardwareSettings.execute())   
        keyboard.add_hotkey('alt+s', lambda: UseScanner.execute("normal"))
        keyboard.add_hotkey('alt+shift+s', lambda: UseScanner.execute("quiet"))
        keyboard.add_abbreviation('adm1', 'https://market.testkontur.ru/AdminTools')
        keyboard.add_abbreviation('adm2', 'https://market-dev.testkontur.ru/AdminTools')
        keyboard.add_abbreviation('csadm1', 'https://market.testkontur.ru/cashboxApi/admin/web/cashbox/')
        keyboard.add_abbreviation('csadm2', 'https://market-dev.testkontur.ru/cashboxApi/admin/web/cashbox/')
        keyboard.add_abbreviation('apidoc', 'https://developer.kontur.ru/')
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
    main()