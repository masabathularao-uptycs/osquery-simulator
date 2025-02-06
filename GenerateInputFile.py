import random, os
import json
from LogicForDistributingAssets import return_asset_distribution
from simulator_config_vars import *
# from datetime import datetime


def shuffle_and_split(lst, n):
    if n <= 0 or len(lst) < n:
        raise ValueError("The number of sublists must be positive and not exceed the list size.")

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


def get_complete_collection(weightage_of_each_table, all_tables,num_records_per_table):
    complete_collection = []
    for table,weightage in zip(all_tables,weightage_of_each_table):
        print(table,weightage*num_records_per_table)
        while weightage:
            complete_collection.append(table)
            weightage-=1
    return complete_collection



def create_single_table_and_its_records(single_message_template, table, recs_per_table):
    with open(OSQUERY_TABLES_TEMPLATE_FILE) as tf:
        osq_template_data = json.load(tf)
    # print(recs_per_table)
    rand_action = random.choice(list(osq_template_data[table].keys()))
    single_message_template["action"] = rand_action
    inside_of_action = osq_template_data[table][rand_action]

    if "variation1" in inside_of_action: #this is probably an events table
        all_variation_keys = list(inside_of_action.keys())
        random_variation_keys = random.choices(all_variation_keys, k=recs_per_table)
        # print(random_variation_keys)

        for each_variation_key in random_variation_keys:
            single_message_template["data"].append(inside_of_action[each_variation_key])
    else:
        for _ in range(recs_per_table):
            single_message_template["data"].append(inside_of_action)
    return single_message_template



def regenerate_same_inputfile(complete_collection_of_all_tables_occurences,dest_file,num_of_msgs_to_form,num_records_per_table):
    print(f"generating inputfile {dest_file}")
    file_to_save = open(dest_file, "w")
    final_collection = shuffle_and_split(complete_collection_of_all_tables_occurences,num_of_msgs_to_form) #splits tables list into chunks, final lenght of list will be equal to num of msgs to form
    # print(final_collection)

    for list_of_tables_for_single_msg in final_collection:
        single_message_template = {"node_key": "11111111-1111-1111-1111-111111111111:5d352099-5f27-5343-bb6a-4282e97d95eb",
                "log_type": "result",
                "data": [],
                "action": ""
                }
        # print("processing : " , msg)
        for table in list_of_tables_for_single_msg:
            # pass
            single_message_template = create_single_table_and_its_records(single_message_template, table, num_records_per_table)
        if single_message_template:
            file_to_save.write(json.dumps(single_message_template))
            file_to_save.write("\n")
    print("regeneration complete")


def main():
    unit_loadtime_in_sec = unit_load_time_in_mins*60
    num_of_msgs_to_form = unit_loadtime_in_sec//DELAY_BETWEEN_TRIGGER
    number_of_tables_to_create = num_of_msgs_to_form*num_tables_per_msg

    print(number_of_tables_to_create)

    with open(OSQUERY_TABLES_TEMPLATE_FILE) as tf:
        osq_template_data = json.load(tf)

    all_tables = list(osq_template_data.keys())

    updated_test_input_params = {
        "num_customers" : len(all_tables),     #this number is the number of unique tables you want to send the load to
        "first_x_customer_percentage":30,       # first x % of tables have
        "load_percentage_for_first_x_percent_customers":60,     #y % weigtage
        "total_number_of_assets":number_of_tables_to_create            # this number is the number of tables to create -> 900/6=150 msgs -> 300secs of load -> 5 mins of load
    }

    weightage_of_each_table,_  = return_asset_distribution(updated_test_input_params)

    print(all_tables)
    print(weightage_of_each_table)
    print(len(weightage_of_each_table))
    print(sum(weightage_of_each_table))

    dest_file = os.path.join(INPUT_FILES_PATH,f"inputfile_{unit_load_time_in_mins}min_{num_of_msgs_to_form}msgs_formed_using_{len(all_tables)}tables_with_ratio_30:60_{num_tables_per_msg}tab_{num_records_per_table}rec.log")
    
    complete_collection_of_all_tables_occurences = get_complete_collection(weightage_of_each_table, all_tables,num_records_per_table) #gives list containing all table names
    regenerate_same_inputfile(complete_collection_of_all_tables_occurences,dest_file,num_of_msgs_to_form,num_records_per_table)

    os.makedirs(INPUTFILES_METADATA_PATH, exist_ok=True)

    file_name_without_suffix = os.path.splitext(os.path.basename(dest_file))[0]
    metadata_filepath = os.path.join(INPUTFILES_METADATA_PATH, file_name_without_suffix+".json")

    metadata_dict = {
        "unit_load_time_in_mins":unit_load_time_in_mins,
        "unit_loadtime_in_sec":unit_loadtime_in_sec,
        "DELAY_BETWEEN_TRIGGER":DELAY_BETWEEN_TRIGGER,
        "num_of_msgs_to_form":num_of_msgs_to_form,
        "number_of_tables_to_create":number_of_tables_to_create,
        "num_tables_per_msg":num_tables_per_msg,
        "num_records_per_table":num_records_per_table,
        "OSQUERY_TABLES_TEMPLATE_FILE":OSQUERY_TABLES_TEMPLATE_FILE,
        "number_of_unique_tables" : len(all_tables),
        "all_tables":all_tables,
        "updated_test_input_params":updated_test_input_params,
        "weightage_of_each_table":weightage_of_each_table,
        "dest_file":os.path.basename(dest_file),
        "complete_collection_of_all_tables_occurences":complete_collection_of_all_tables_occurences,
    }

    with open(metadata_filepath, "w") as m_f:
        json.dump(metadata_dict, m_f, indent=4)


    

if __name__ == "__main__":
    main()
        