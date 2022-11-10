from helpers import fileshelper
import pyperclip

cashboxId = fileshelper.getCashboxId()
pyperclip.copy(cashboxId)
fileshelper.startCashbox()