import json
import config

def init_json_file():
    data = {
        "hospitals":[]
    }
    with open(config.args_file, "w") as file:
        json.dump(data,file)


def del_hospital_json(name: str)->bool:
    try:
        file = open(config.args_file)
        data = json.load(file)
        data["hospitals"]
    except:
        init_json_file()
        return False

    for hosp in data["hospitals"]:
        if(list(hosp.keys())[0]==name):
            data["hospitals"].remove(hosp)
            print(data)
            with open(config.args_file, "w") as file:
                json.dump(data, file)
            return True
    return False


def add_hospital(hosp)->None:
    try:
        file = open(config.args_file)
        data = json.load(file)
        data["hospitals"].append(hosp)
    except:
        init_json_file()
        add_hospital(hosp)
        return
    with open(config.args_file, "w") as file:
        json.dump(data, file)


def print_all_hospitals()->str:
    try:
        file = open(config.args_file)
        data = json.load(file)
        data["hospitals"]
    except:
        init_json_file()
        print_all_hospitals()
        return ""
    ans: str = ""
    line: str
    for hosp in data["hospitals"]:
        name = list(hosp.keys())[0]
        title = name + ":\n"
        body = "\t- ИНН: " + hosp[name]["inn"] + "\n" + "\t- Ключевые слова: "
        keys = ""
        for key in hosp[name]["keys_words"]:
            keys += key + ", "
        line = title + body + keys + "\n"
        ans += line
    return ans