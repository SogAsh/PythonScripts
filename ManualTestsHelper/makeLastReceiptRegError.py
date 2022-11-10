from helpers import fileshelper
import json

con = fileshelper.setDbConnection()
(id, shiftId, number, content) = fileshelper.getLastReceipt(con)
receipt = json.loads(content)
receipt["kkmRegistrationStatus"] = "Error"
receipt["correctionReceiptId"] = None
fileshelper.updateReceiptContent(con, json.dumps(receipt), id)
con.close()
fileshelper.startCashbox()