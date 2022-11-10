import pyperclip
from helpers import fileshelper

cashboxId = pyperclip.paste()
fileshelper.writeJsonValue("cashboxId", cashboxId)