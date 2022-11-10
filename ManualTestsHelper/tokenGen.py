from helpers import nethelper
from helpers import fileshelper

cashboxId = fileshelper.getCashboxId()
session = nethelper.startSession()
nethelper.genToken(session, cashboxId)
fileshelper.startCashbox()
