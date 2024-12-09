import json
import random
from simulator_config_vars import HOSTNAMES_FILES_PATH,hostname


def generate_names(instance:dict, createNew: bool) -> dict:
    clients = instance["clients"]
    domain = instance["domain"]
    suffix = random.randint(1,100)
    prefix = random.randint(1,100)
    
    if createNew or "names" not in instance:
        file = f"{domain}_names_{prefix}{suffix}.txt"
        instance["names"] = file

    file = f"{HOSTNAMES_FILES_PATH}/{instance['names']}" 

    with open(file, "w") as f:
        for i in range(clients):
            name = f"test-{domain}-{hostname}-{i+1}-{prefix}{suffix}\n"
            f.write(name)
    return instance


def generate(testinput_file):
    print
    with open(testinput_file, 'r') as file:
        data = json.load(file)
        for instance in data["instances"]:
            instance = generate_names(instance, False)  
        
    with open(testinput_file, "w") as file:
        file.write(json.dumps(data, indent=4))
        
if __name__ == "__main__":
    generate()
        