import random, os
import json, re
from LogicForDistributingAssets import return_asset_distribution
from simulator_config_vars import *
from OrderTemplateFile_AccordingToProductionTables import order_template_file
# from datetime import datetime


def shuffle_and_split(lst, n):
    if n <= 0 or len(lst) < n:
        raise ValueError("The number of sublists must be positive and not exceed the list size.")

    if not __name__ == "__main__":
        random.shuffle(lst)  # Shuffle the list in place
    
    # Compute size of each bucket
    bucket_size = len(lst) // n
    remainder = len(lst) % n

    # Create sublists of equal size, distributing the remainder evenly
    result = []
    start = 0
    for i in range(n):
        end = start + bucket_size + (1 if i < remainder else 0)
        result.append(lst[start:end])
        start = end
    
    return result


def get_complete_collection(weightage_mapping):
    complete_collection = []
    for table,weightage in weightage_mapping.items():
        while weightage:
            complete_collection.append(table)
            weightage-=1
    return complete_collection



def create_single_table_and_its_records(single_message_template, table, recs_per_table, tables_template_file):
    with open(tables_template_file) as tf:
        osq_template_data = json.load(tf)

    if __name__ == "__main__":
        rand_action = "added"
    else:
        rand_action = random.choice(list(osq_template_data[table].keys()))
    single_message_template["action"] = rand_action
    inside_of_action = osq_template_data[table][rand_action]

    if "variation1" in inside_of_action:  # This is probably an events table
        all_variation_keys = list(inside_of_action.keys())
        # random_variation_keys = random.choices(all_variation_keys, k=recs_per_table)
        # Generate sequential keys with wrapping if the list length is smaller than recs_per_table
        sequential_variation_keys = [all_variation_keys[i % len(all_variation_keys)] for i in range(recs_per_table)]

        for each_variation_key in sequential_variation_keys:
            single_message_template["data"].append(inside_of_action[each_variation_key])
    else:
        for _ in range(recs_per_table):
            single_message_template["data"].append(inside_of_action)


def regenerate_same_inputfile(weightage_mapping, save_input_file_to, num_of_msgs_to_form, num_records_per_table, tables_template_file):
    print(f"Generating input file: {save_input_file_to}")
    
    complete_collection_of_all_tables_occurences = get_complete_collection(weightage_mapping) #gives list containing all table names
    final_collection = shuffle_and_split(complete_collection_of_all_tables_occurences, num_of_msgs_to_form)
    
    with open(save_input_file_to, "w") as file_to_save:
        for list_of_tables_for_single_msg in final_collection:
            single_message_template = {
                "node_key": "",
                "log_type": "result",
                "data": [],
                "action": ""
            }
            
            for table in list_of_tables_for_single_msg:
                create_single_table_and_its_records(single_message_template, table, num_records_per_table, tables_template_file)

            if single_message_template["data"]:  # Check if the message has valid data
                # json.dump(single_message_template, file_to_save)
                file_to_save.write(json.dumps(single_message_template)) # this method is faster than above
                file_to_save.write("\n")
            else:
                print("ERROR : Message is not populated")
                raise(f"ERROR : Message is not populated for tables list : {list_of_tables_for_single_msg}")

                
    print("Regeneration complete.")

def get_expected_events(save_input_file_to,trans=True):
    dns_lookup_events = {'dns_lookup_events-builder-added':0, 'dns_lookup_events_1-builder-added':0, 'dns_lookup_events_2-builder-added':0, 'dns_lookup_events_3-builder-added':0, 'dns_lookup_events_4-builder-added':0,'dns_lookup_events_5-builder-added':0,'dns_lookup_events_6-builder-added':0}
    process_events = {'process_events-builder-added':0, 'process_events_1-builder-added':0, 'process_events_2-builder-added':0, 'process_events_3-builder-added':0, 'process_events_4-builder-added':0, 'process_events_5-builder-added':0, 'process_events_6-builder-added':0, 'process_events_7-builder-added':0, 'process_events_8-builder-added':0, 'process_events_9-builder-added':0, 'process_events_10-builder-added':0}
    socket_events = {'socket_events-builder-added':0, 'socket_events_1-builder-added':0, 'socket_events_2-builder-added':0, 'socket_events_3-builder-added':0, 'socket_events_4-builder-added':0, 'socket_events_5-builder-added':0, 'socket_events_6-builder-added':0,'socket_events_7-builder-added':0}
    process_file_events = {'process_file_events-builder-added':0, 'process_file_events_3-builder-added':0, 'process_file_events_4-builder-added':0, 'process_file_events_5-builder-added':0, 'process_file_events_6-builder-added':0, 'process_file_events_7-builder-added':0, 'process_file_events_8-builder-added':0, 'process_file_events_9-builder-added':0, 'process_file_events_10-builder-added':0}
    req_tables = ['process_events', 'process_file_events', 'socket_events', 'dns_lookup_events']
    increment=1
    with open(save_input_file_to, "r") as fin:
        for line in fin:
            lines = json.loads(line)
            #print(line)
            #print(len(lines["data"]))
            for table_details in lines["data"]:
                #print(table_details)
                if table_details['name'] == 'process_events':
                    # index1 = table_details['columns']['auid']
                    # index2 = table_details['columns']['uid']
                    #rows = table_details['rows']
                    # if index1 == '0' or index2 == '0':
                    if ("auid" in table_details['columns'] and table_details['columns']['auid'] == '0') or ( 'uid' in table_details['columns'] and table_details['columns']['uid'] == '0'):
                        process_events['process_events-builder-added'] += increment
                    if '/bin/sh' in table_details['columns']['path']:
                        if '/bin/mysql' in table_details['columns']['ancestor_list']:
                            process_events['process_events_5-builder-added'] += increment
                        if '/bin/php' in table_details['columns']['ancestor_list']:
                            process_events['process_events_1-builder-added'] += increment
                        if '/bin/awk' in table_details['columns']['ancestor_list']:
                            process_events['process_events_10-builder-added'] += increment
                    if '/proc/' in table_details['columns']['cmdline']:
                        process_events['process_events_2-builder-added'] += increment
                    if 'base64' in table_details['columns']['cmdline']:
                        process_events['process_events_3-builder-added'] += increment
                    if ('bin/osascript' in table_details['columns']['path']) or ('shell' in table_details['columns']['cmdline']):
                        process_events['process_events_4-builder-added'] += increment
                    if table_details['columns']['exe_name'] == 'wmic.exe':
                        process_events['process_events_7-builder-added'] += increment
                    # if table_details['columns']['version_info'] == "Net Command":
                    if "version_info" in table_details['columns'] and table_details['columns']['version_info'] == "Net Command":
                        process_events['process_events_8-builder-added'] += increment
                    if 'rmmod' in table_details['columns']['cmdline']:
                        process_events['process_events_9-builder-added'] += increment
                if table_details['name'] == 'socket_events':
                    if (table_details['columns']['action'] == 'connect') and (table_details['columns']['family'] == '2') and (table_details['columns']['type'] == '2') and (table_details['columns']['exe_name'] == 'node'):
                        socket_events['socket_events-builder-added'] += increment
                        socket_events['socket_events_1-builder-added'] += increment
                        socket_events['socket_events_2-builder-added'] += increment
                    if (table_details['columns']['action'] == 'connect') and (table_details['columns']['family'] == '2') and (table_details['columns']['type'] == '2') and (table_details['columns']['remote_address'] == '169.254.169.254') and (table_details['columns']['is_container_process'] == '1'):
                        socket_events['socket_events_3-builder-added'] += increment
                    if (table_details['columns']['action'] == 'connect') and (table_details['columns']['cmdline'] == '-e') and (table_details['columns']['path'] == '/usr/bin/ruby'):
                        socket_events['socket_events_4-builder-added'] += increment
                    if "9.5.4.3" in table_details['columns']['remote_address'] or "169.254.169.254" in table_details['columns']['remote_address']:
                        socket_events['socket_events_5-builder-added'] += increment
                    if "9.5.4.3" in table_details['columns']['remote_address']:
                        socket_events['socket_events_6-builder-added'] += increment
                    if "ruby" in table_details["columns"]["path"]:
                        socket_events['socket_events_7-builder-added'] += increment

                if table_details['name'] == 'dns_lookup_events':
                    #print(table_details["columns"])
                    index = table_details['columns']['question']
                    index1=table_details['columns']['answer']
                    last_part = index1.split('.')[-1]
                    #print(last_part)
                    num_list=re.findall("[0-9]", last_part)
                    #rows = table_details['rows']
                    #for row in rows:
                    if 'malware' in index:
                        dns_lookup_events['dns_lookup_events_1-builder-added'] += increment
                        dns_lookup_events['dns_lookup_events_2-builder-added'] += increment
                    if 'dga' in index:
                        dns_lookup_events['dns_lookup_events_3-builder-added'] += increment
                    if 'phishing' in index:
                        dns_lookup_events['dns_lookup_events_4-builder-added'] += increment
                    if 'coinminer' in index:
                        dns_lookup_events['dns_lookup_events-builder-added'] += increment  
                    if  len(last_part) == len(num_list):
                        dns_lookup_events['dns_lookup_events_6-builder-added'] += increment     
                    if len(index)>7:
                        dns_lookup_events['dns_lookup_events_5-builder-added'] += increment
                        
    

                if table_details['name'] == 'process_file_events':
                    #rows = table_details['rows']
                    #for row in rows:
                    if (table_details['columns']['path'] == '/etc/passwd') and (table_details['columns']['operation'] == 'open') and (table_details['columns']['flags'] == 'O_WRONLY'):
                        process_file_events['process_file_events_3-builder-added'] += increment
                        process_file_events['process_file_events_4-builder-added'] += increment
                    if (table_details['columns']['operation'] == 'chmod') and (table_details['columns']['flags'] == 'S_ISUID'):
                        process_file_events['process_file_events-builder-added'] += increment
                    if (table_details['columns']['operation'] == 'rename') and (table_details['columns']['dest_path'] == '/.'):
                        process_file_events['process_file_events_5-builder-added'] += increment
                    if table_details['columns']['operation'] == 'chown32':
                        process_file_events['process_file_events_6-builder-added'] += increment
                    if (table_details['columns']['operation'] == 'write') and (table_details['columns']['executable'] == 'System') and (('.exe' in table_details['columns']['path']) or ('4D5A9000' in table_details['columns']['magic_number'])):
                        process_file_events['process_file_events_7-builder-added'] += increment
                    if (table_details['columns']['operation'] == 'rename'):
                        process_file_events['process_file_events_8-builder-added'] += increment
                    if ('/etc/ld.so.conf' in table_details['columns']['path']) and (table_details['columns']['operation'] == 'open') and (table_details['columns']['flags'] == 'O_WRONLY'):
                        process_file_events['process_file_events_9-builder-added'] += increment
                    if (table_details['columns']['path'] == '/etc/passwd') and (table_details['columns']['operation'] == 'open') and (table_details['columns']['is_container_process'] == '0'):
                        process_file_events['process_file_events_10-builder-added'] += increment

            
        dict1 = {}
        dict1.update(dns_lookup_events)
        dict1.update(process_events)
        dict1.update(socket_events)
        dict1.update(process_file_events)
        if not trans:
            transformations=["dns_lookup_events_5-builder-added","dns_lookup_events_6-builder-added","dns_lookup_events_7-builder-added","socket_events_7-builder-added","socket_events_8-builder-added"]
            keys=dict1.keys()
            for events in keys:
                if events in transformations:
                    dict1[events]=0        
        return dict1

def main():
    order_template_file()
    number_of_tables_to_create = NUMBER_OF_MSGS_PER_INPUTFILE*NUMBER_OF_TABLES_PER_MSG
    
    print(number_of_tables_to_create)

    with open(OSQUERY_TABLES_TEMPLATE_FILE) as tf:
        osq_template_data = json.load(tf)

    all_tables = list(osq_template_data.keys())

    updated_test_input_params = {
        "num_customers" : len(all_tables),     #this number is the number of unique tables you want to send the load to
        "first_x_customer_percentage":FIRST_X_PERCENT_TABLES,       # first x % of tables have
        "load_percentage_for_first_x_percent_customers":GETS_Y_PERCENT_WEIGHTAGE,     #y % weigtage
        "total_number_of_assets":number_of_tables_to_create            # this number is the number of tables to create -> 900/6=150 msgs -> 300secs of load -> 5 mins of load
    }

    weightage_of_each_table,_  = return_asset_distribution(updated_test_input_params)

    print(all_tables)
    print(weightage_of_each_table)
    print(len(weightage_of_each_table))
    print(sum(weightage_of_each_table))

    save_input_file_to = os.path.join(INPUT_FILES_PATH,f"inputfile_{calculated_unit_load_time_in_mins}min_{NUMBER_OF_MSGS_PER_INPUTFILE}msgs_formed_using_{len(all_tables)}tables_with_ratio_{FIRST_X_PERCENT_TABLES}:{GETS_Y_PERCENT_WEIGHTAGE}_{NUMBER_OF_TABLES_PER_MSG}tab_{NUMBER_OF_RECORDS_PER_TABLE}rec.log")
    weightage_mapping = dict(zip(all_tables, weightage_of_each_table))
    # complete_collection_of_all_tables_occurences = get_complete_collection(weightage_mapping) #gives list containing all table names
    regenerate_same_inputfile(weightage_mapping,save_input_file_to,NUMBER_OF_MSGS_PER_INPUTFILE,NUMBER_OF_RECORDS_PER_TABLE,OSQUERY_TABLES_TEMPLATE_FILE)

    os.makedirs(INPUTFILES_METADATA_PATH, exist_ok=True)

    file_name_without_suffix = os.path.splitext(os.path.basename(save_input_file_to))[0]
    metadata_filepath = os.path.join(INPUTFILES_METADATA_PATH, file_name_without_suffix+".json")

    metadata_dict = {
        "calculated_unit_load_time_in_mins":calculated_unit_load_time_in_mins,
        "number_of_msgs_this_inputfile_contains":NUMBER_OF_MSGS_PER_INPUTFILE,
        "number_of_tables_per_msg":NUMBER_OF_TABLES_PER_MSG,
        "total_number_of_tables_including_duplicates":number_of_tables_to_create,
        "tables_template_file":OSQUERY_TABLES_TEMPLATE_FILE,
        "total_number_of_unique_tables" : len(all_tables),
        "distribution_logic_params":updated_test_input_params,
        "weightage_mapping" : weightage_mapping,
        "number_of_records_per_table":NUMBER_OF_RECORDS_PER_TABLE,
        "expected_records_for_each_table":{table:weightage*NUMBER_OF_RECORDS_PER_TABLE for table,weightage in zip(all_tables,weightage_of_each_table)},
        "expected_events_counts":get_expected_events(save_input_file_to),
        "save_input_file_to":os.path.basename(save_input_file_to),
        # "complete_collection_of_all_tables_occurences":complete_collection_of_all_tables_occurences,
    }

    with open(metadata_filepath, "w") as m_f:
        json.dump(metadata_dict, m_f, indent=4)


    

if __name__ == "__main__":
    main()
        