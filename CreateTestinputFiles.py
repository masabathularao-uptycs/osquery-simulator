import os
import json
from LogicForDistributingAssets import return_asset_distribution
from simulator_config_vars import *
from test_input_params import test_input_params
from CollectSecretkeys import collect_secretkeys


def split_instances_nearly_equal_sum(data, simulators, return_dict):
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
    sublist_domains = [[] for _ in range(n)]
    # Distribute each dictionary greedily
    for item in data:
        # Find index of the sublist with the smallest sum
        min_sum_index = sublist_sums.index(min(sublist_sums))
        
        # Add the item to that sublist
        sublists[min_sum_index].append(item)
        sublist_clients[min_sum_index].append(item["clients"])
        sublist_domains[min_sum_index].append(item["domain"])
        # Update the sum of that sublist
        sublist_sums[min_sum_index] += item["clients"]

    print("Asset distribution for each simulator : ")
    for i,sim in enumerate(simulators):
        combined_clients = list(zip(sublist_domains[i], sublist_clients[i]))
        # print(f"simulator {sim} -> (sum={sublist_sums[i]}) -> clients list = {combined_clients}")
        return_dict[f"simulator '{sim}' instance list: (assets={sublist_sums[i]})"] = combined_clients
    return sublists

def create_testinput_files(updated_test_input_params, do_update = False):
    assets_to_enrol_for_each_customer,return_dict  = return_asset_distribution(updated_test_input_params)

    stack_json_file_path = f"{STACK_JSONS_PATH}/{updated_test_input_params['stack_json_file']}"

    with open(stack_json_file_path,'r') as json_file:
        json_file = json.load(json_file)
    simulators =  json_file["osquery_data_load_params"]["sims"]
    base_domain = json_file["domain"]
    configdb_node = json_file["configdb_node"]

    return_dict["3. Number of simulators configured"] = len(simulators)

    if not os.path.exists(f"{SECRETS_JSONS_PATH}/{base_domain}.json"):
        print(f"Secrets not found for {base_domain}, collecting secret keys...")
        collect_secretkeys(configdb_node,base_domain)

    with open(f"{SECRETS_JSONS_PATH}/{base_domain}.json",'r') as secrets_file_obj:
        secrets_dict = json.load(secrets_file_obj)
        print(f"secrets for {base_domain} loaded")
    instances = []

    for i in range(updated_test_input_params["num_customers"]):
        if i==0:
            domain = base_domain
        else:
            domain = base_domain+str(i)

        clients_to_enrol_to_this_cust = int(assets_to_enrol_for_each_customer[i])
        while clients_to_enrol_to_this_cust>0:
            instances.append({
                "instanceid":i+1,
                "domain":domain,
                "secret":secrets_dict[domain],
                "clients":300 if clients_to_enrol_to_this_cust>=300 else clients_to_enrol_to_this_cust,
                "port":30001+i,
                # "names":"names.txt"
            })
            clients_to_enrol_to_this_cust-=300

    # split_instances = np.array_split(instances, len(simulators))
    # split_instances = [list(arr) for arr in split_instances]

    split_instances = split_instances_nearly_equal_sum(instances, simulators, return_dict)
    print(return_dict)

    if not do_update:
        return return_dict
    for one_instance_list,simulator_name in zip(split_instances,simulators):
        os.makedirs(TESTINPUT_FILES_PATH, exist_ok=True)
        final_testinput_content = {"instances":one_instance_list}
        # final_testinput_content.update(updated_test_input_params)
        with open(f"{TESTINPUT_FILES_PATH}/{simulator_name}_testinput.json",'w') as f:
            json.dump(final_testinput_content, f, indent=4)
        print(f"****  Testinput file for {simulator_name} is created. testinput file name is : {TESTINPUT_FILES_PATH}/{simulator_name}_testinput.json")
    return return_dict

if __name__ == "__main__":
    create_testinput_files(test_input_params,do_update=True)
