import json

def getDataForJson():
    data = {}
    data["configPath"] = ""
    data["diskDrives"] = ["C:\\","D:\\","F:\\"]
    data["cashboxId"] = ""
    return json.dumps(data, indent=4)

with open("data.json", "w") as file:
    data = getDataForJson()
    file.write(data) 