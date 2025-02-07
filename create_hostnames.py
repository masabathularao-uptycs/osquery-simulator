import json
# import random
from simulator_config_vars import HOSTNAMES_FILES_PATH,hostname
import uuid
import os

def generate_names(instance:dict, createNew: bool) -> dict:
    clients = instance["clients"]
    domain = instance["domain"]
    instance_id = instance["instanceid"]
    # suffix = random.randint(1,100)
    # prefix = random.randint(1,100)
    
    if createNew or "names" not in instance:
        file = f"{domain}_names_{uuid.uuid4()}_{clients}_{instance_id}.txt"
        instance["names"] = file

    file = f"{HOSTNAMES_FILES_PATH}/{instance['names']}" 
    
    with open(file, "w") as f:
        for i in range(clients):
            name = f"test-{domain}-{hostname}-{i+1}-{clients}_{instance_id}\n"
            f.write(name)
    return instance


def generate(testinput_file):
    os.makedirs(HOSTNAMES_FILES_PATH,exist_ok=True)
    print
    with open(testinput_file, 'r') as file:
        data = json.load(file)
        for instance in data["instances"]:
            instance = generate_names(instance, False)  
        
    with open(testinput_file, "w") as file:
        file.write(json.dumps(data, indent=4))
        
if __name__ == "__main__":
    generate()
        