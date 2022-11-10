from helpers import nethelper
from helpers import fileshelper

cashboxId = fileshelper.getCashboxId()
session = nethelper.startSession()
settings = nethelper.getCashoxSettingsJson(session, cashboxId)
flippedSettings = nethelper.flipBoolSettings(settings, "moveRemainsToNextShift")
nethelper.postCashboxSettings(session, cashboxId, flippedSettings)
fileshelper.startCashbox()