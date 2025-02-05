import random, os
import json
from LogicForDistributingAssets import return_asset_distribution
from simulator_config_vars import *
# from datetime import datetime

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


def get_complete_collection(weightage_of_each_table, all_tables):
    complete_collection = []
    for table,weightage in zip(all_tables,weightage_of_each_table):
        while weightage:
            complete_collection.append(table)
            weightage-=1
    return complete_collection

final_collection = shuffle_and_split(get_complete_collection(weightage_of_each_table, all_tables),num_of_msgs_to_form)
print(final_collection)


# now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

dest_file = os.path.join(INPUT_FILES_PATH,f"inputfile_{unit_load_time_in_mins}min_{num_of_msgs_to_form}msgs_formed_using_{len(all_tables)}tables_with_ratio_30:60_{num_tables_per_msg}tab_{num_records_per_table}rec.log")
out_fd = open(dest_file, "w")


def create_record_for_grpc_orig(js_line, table, recs_per_table):
    # print(recs_per_table)
    rand_action = random.choice(list(osq_template_data[table].keys()))
    js_line["action"] = rand_action
    tmp = osq_template_data[table][rand_action]
    
    tmp_data={}
    
    if js_line:
        if "variation1" not in tmp:
            for _ in range(recs_per_table):
                js_line["data"].append(tmp)
        else:
            keys = list(tmp.keys())
            random_keys = random.choices(keys, k=recs_per_table)
            print(random_keys)
            for each_key in random_keys:
                if tmp[each_key]:
                    tmp_data=tmp[each_key]
                    js_line["data"].append(tmp[each_key])
                else:
                    if tmp_data:
                        js_line["data"].append(tmp_data)

    return js_line

for msg in final_collection:
    js_line = {"node_key": "11111111-1111-1111-1111-111111111111:5d352099-5f27-5343-bb6a-4282e97d95eb",
            "log_type": "result",
            "data": [],
            "action": ""
            }
    # print("processing : " , msg)
    for table in msg:
        # pass
        js_line = create_record_for_grpc_orig(js_line, table, num_records_per_table)
    if js_line:
        # print("writing")
        # out_fd.write(now)
        # out_fd.write("\n")
        out_fd.write(json.dumps(js_line))
        out_fd.write("\n")
