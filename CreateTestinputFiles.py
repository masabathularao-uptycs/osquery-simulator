import os
import json
from LogicForDistributingAssets import return_asset_distribution
from simulator_config_vars import *
from test_input_params import test_input_params
from CollectSecretkeys import collect_secretkeys


def split_instances_nearly_equal_sum(data, simulators):
    n=len(simulators)
    """
    Split a list of dictionaries into 'n' sublists with nearly equal sum of 'clients'.
    
    Args:
        data: List of dictionaries with a 'clients' key.
        n: Number of groups to split the list into.
    
    Returns:
        A list of 'n' sublists with nearly equal sums of 'clients'.
    """
    # Sort data by 'clients' in descending order
    data = sorted(data, key=lambda x: x["clients"], reverse=True)

    # Initialize n empty sublists and their sums
    sublists = [[] for _ in range(n)]
    sublist_sums = [0] * n  # Track the sums of each sublist
    sublist_clients = [[] for _ in range(n)]
    # Distribute each dictionary greedily
    for item in data:
        # Find index of the sublist with the smallest sum
        min_sum_index = sublist_sums.index(min(sublist_sums))
        
        # Add the item to that sublist
        sublists[min_sum_index].append(item)
        sublist_clients[min_sum_index].append(item["clients"])
        # Update the sum of that sublist
        sublist_sums[min_sum_index] += item["clients"]

    print("Asset distribution for each simulator : ")
    for i,sim in enumerate(simulators):
        print(f"simulator {sim} -> (sum={sublist_sums[i]}) -> clients list = {sublist_clients[i]}")
    return sublists

def create_testinput_files(stack_json_file_name):
    stack_json_file_path = f"{STACK_JSONS_PATH}/{stack_json_file_name}"

    with open(stack_json_file_path,'r') as json_file:
        json_file = json.load(json_file)
    osquery_data_load_params =  json_file["osquery_data_load_params"]
    base_domain = json_file["domain"]
    configdb_node = json_file["configdb_node"]

    simulators = osquery_data_load_params["sims"]

    assets_to_enrol_for_each_customer  = return_asset_distribution(test_input_params["num_customers"],test_input_params["first_x_customer_percentage"],test_input_params["load_percentage_for_first_x_percent_customers"],test_input_params["total_number_of_assets"])

    if not os.path.exists(f"{SECRETS_JSONS_PATH}/{base_domain}.json"):
        print(f"Secrets not found for {base_domain}, collecting secret keys...")
        collect_secretkeys(configdb_node,base_domain)

    with open(f"{SECRETS_JSONS_PATH}/{base_domain}.json",'r') as secrets_file_obj:
        secrets_dict = json.load(secrets_file_obj)
        print(f"secrets for {base_domain} loaded")
    instances = []

    for i in range(test_input_params["num_customers"]):
        if i==0:
            domain = base_domain
        else:
            domain = base_domain+str(i)
        instances.append({
            "instanceid":i+1,
            "domain":domain,
            "secret":secrets_dict[domain],
            "clients":int(assets_to_enrol_for_each_customer[i]),
            "port":30001+i,
            # "names":"names.txt"
        })

    # split_instances = np.array_split(instances, len(simulators))
    # split_instances = [list(arr) for arr in split_instances]

    split_instances = split_instances_nearly_equal_sum(instances, simulators)
    
    for one_instance_list,simulator_name in zip(split_instances,simulators):
        os.makedirs(TESTINPUT_FILES_PATH, exist_ok=True)
        final_testinput_content = {"instances":one_instance_list}
        # final_testinput_content.update(test_input_params)
        with open(f"{TESTINPUT_FILES_PATH}/{simulator_name}_testinput.json",'w') as f:
            json.dump(final_testinput_content, f, indent=4)
        print(f"Testinput file for {simulator_name} is created. testinput file name is : {TESTINPUT_FILES_PATH}/{simulator_name}_testinput.json")


if __name__ == "__main__":
    create_testinput_files(test_input_params["stack_json_file"])
