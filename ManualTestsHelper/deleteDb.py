import os
from helpers import fileshelper

cashboxPath = fileshelper.findCashboxPath()
dbPath = os.path.join(cashboxPath, "db")
fileshelper.deleteFolder(dbPath)