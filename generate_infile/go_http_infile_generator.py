import sys
import json
from datetime import datetime
import random

count = 'one'

def remove_data(data, table):
    _data = []
    for event in data:
        if table == "process_open_sockets":
            if event["name"].find(table) == -1:
                _data.append(event)
        else:
            if event["name"] != table:
                _data.append(event)
    return _data


def add_record_mul_times(record, repeats):
    _data = []
    for i in range(repeats):
        _data.append(record)
    return _data


def add_record_mul_times_grpc(grpc_rec, record):
    added = True if record["action"] == "added" else False
    grpc_rec["added"].append(added)
    row = list(record["columns"].values())
    grpc_rec['rows'].append(row)
    return grpc_rec

def add_record_mul_times_grpc_orig(grpc_rec, record):
    added = True if record["action"] == "added" else False
    grpc_rec["added"].append(added)
    grpc_rec["rows"].append(list(record["columns"].values()))
    return grpc_rec

def create_record_for_grpc_orig(js_line, table, recs_per_table):
    print(recs_per_table)
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

def create_record_for_grpc(js_line, table, recs_per_table):
    js_line = create_record_for_grpc_orig(js_line, table, recs_per_table)
    return js_line
   

if len(sys.argv) < 3:
    print("Usage: python gen_custom_input_file.py <no_lines> <tables_per_msg> <recs_per_tables>")
    sys.exit(1)

osquery_template_file = "new_file_ancestor_bkp3.json"
with open(osquery_template_file) as tf:
    osq_template_data = json.load(tf)

dest_file = "rhel_6tab_12rec_fix.log"
lines = int(sys.argv[1])
tables_per_msg = int(sys.argv[2])
recs_per_table = int(sys.argv[3])
out_fd = open(dest_file, "w")
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
for line in range(lines):
    js_line = {"node_key": "11111111-1111-1111-1111-111111111111:5d352099-5f27-5343-bb6a-4282e97d95eb",
                "log_type": "result",
                "data": [],
                "action": ""
                }
    event_tables=["dns_lookup_events", "process_events", "process_file_events", "socket_events"]
    rand_tables=random.sample(list(osq_template_data.keys()), tables_per_msg)
    loop_count=1
    while len(rand_tables)<tables_per_msg and loop_count<=4:
        print("warning while loop")
        temp_tab=random.sample(event_tables, 1)
        if temp_tab not in rand_tables:
            rand_tables.append(temp_tab[0])
        loop_count+=1
    print(rand_tables)
    if len(rand_tables)!=tables_per_msg:
        print("got error")
        #rand_tables.append(temp_tab)
    for table in rand_tables:
        js_line = create_record_for_grpc(js_line, table, recs_per_table)
    #print(js_line)
    if js_line:
        out_fd.write(now)
        out_fd.write("\n")
        out_fd.write(json.dumps(js_line))
        out_fd.write("\n")
        continue
out_fd.close()