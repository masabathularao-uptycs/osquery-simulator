import time
import sys
import datetime
import json
import logging
import _thread
# import threading
import requests
from simulator_config_vars import *
import os
from GenerateInputFile import regenerate_same_inputfile
import random
import pandas as pd

global datastats_action
global record_count

record_count=0
datastats_action={}
datastats={}
statsflag=True

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',  # Write logs to this file
    filemode='w'  # Overwrite the log file on each run; use 'a' to append
)

LOCAL_HOST = "127.0.0.1"

def analyse(message):
        global record_count
        pydict=json.loads(message)
        #logging.info("No of records : ",len(pydict['data']))
        for record in pydict['data']:
            record_count +=1
            table_name = record['name']
            if table_name not in datastats_action: 
                datastats_action[table_name]={"added":0,"removed":0,"snapshot":0}
                datastats_action[table_name][record["action"]]+=1
            else:
                datastats_action[table_name][record["action"]]+=1

            if table_name not in datastats:
                datastats[table_name] =1
            else:
                datastats[table_name] +=1

def actual_send(msg,port):
      x = requests.post(f"http://{LOCAL_HOST}:"+str(port), data=msg)
      #logging.info(dir(x))
      #logging.info(x.status_code)
      #logging.info(x.url)

def SendTrigger(msg,portlist):
    for Port in portlist:
      _thread.start_new_thread(actual_send, (msg,Port))

try:
   with open(testinput_file) as f:
      data = f.read()
      testinput_contents= json.loads(data)
except Exception as e:
    logging.critical(f"Error occured while processing  {testinput_file}",e)
    sys.exit(1)
    
all_instances=testinput_contents['instances']
portlist=[]
for eachinstance in all_instances:
   portlist.append(eachinstance['port'])

# duration_of_load_in_sec = testinput_contents['duration_of_load_in_sec']
# how_many_msgs_to_send = duration_of_load_in_sec // DELAY_BETWEEN_TRIGGER

how_many_msgs_to_send = testinput_contents['how_many_msgs_to_send']

saved_how_many_msgs_to_send = how_many_msgs_to_send

start_time = time.time()
iteration_count = 0
regeneration_count = 0
total_analyse_time = 0
metadata_contents = None
decayed_delay_trigger = DELAY_BETWEEN_TRIGGER

input_file_path = os.path.join(INPUT_FILES_PATH, testinput_contents['inputfile'])

if not os.path.isfile(input_file_path):
    logging.warning(f"Input File '{input_file_path}' does not exist.")
    with open(OSQUERY_TABLES_TEMPLATE_FILE) as tf:
        osq_template_data = json.load(tf)
    if testinput_contents['inputfile'] in osq_template_data:
        table_name = testinput_contents['inputfile']
        logging.info(f"Valid Table name found {table_name}. Creating msg using this table.")

        while how_many_msgs_to_send:
            single_message_template = {"node_key": "11111111-1111-1111-1111-111111111111:5d352099-5f27-5343-bb6a-4282e97d95eb",
                            "log_type": "result",
                            "data": [],
                            "action": ""
                            }
            rand_action = random.choice(list(osq_template_data[table_name].keys()))
            single_message_template["action"] = rand_action
            inside_of_action = osq_template_data[table_name][rand_action]

            if "variation1" in inside_of_action: #this is probably an events table
                all_variation_keys = list(inside_of_action.keys())
                random_variation_keys = random.choices(all_variation_keys, k=num_records_per_table*num_tables_per_msg)
                # logging.info(f"Random variation keys are : {random_variation_keys}")

                for each_variation_key in random_variation_keys:
                    single_message_template["data"].append(inside_of_action[each_variation_key])
            else:
                for _ in range(num_records_per_table*num_tables_per_msg):
                    single_message_template["data"].append(inside_of_action)
            unix_timestamp=int(time.time())
            final_message = f"{unix_timestamp}{json.dumps(single_message_template)}"
            # logging.info(single_message_template)
            analyse(json.dumps(single_message_template))  # Analyze the current message      
            _thread.start_new_thread(SendTrigger, (final_message,portlist))
            how_many_msgs_to_send-=1
            logging.info(f"Msg sent(built using {table_name} table)! {how_many_msgs_to_send} remaining, Timestamp : {unix_timestamp}")
            time.sleep(decayed_delay_trigger)
    else:
        logging.error(f"'{testinput_contents['inputfile']}' table not found in {OSQUERY_TABLES_TEMPLATE_FILE} either")
        sys.exit(1)


    

else:
  Time=TIME.split('-')
  if Time[0] == '0000':
    unix_timestamp=int(time.time())
    logging.info(f"year provided is {Time[0]}, new unix_timestamp generated is : {unix_timestamp}")
  else:
    year,month,day,hr,minute=int(Time[0]),int(Time[1]),int(Time[2]),int(Time[3]),int(Time[4])
    datetime_object = datetime.datetime(year,month,day,hr,minute)
    unix_timestamp = int(time.mktime(datetime_object.timetuple()))
    logging.info(f"year provided is {Time[0]}, so using provided unix_timestamp : {unix_timestamp}")


  file_name_without_suffix = os.path.splitext(os.path.basename(input_file_path))[0]
  metadata_filepath = os.path.join(INPUTFILES_METADATA_PATH, file_name_without_suffix+".json")
  logging.info(f"metadata_filepath : {metadata_filepath}")

  if os.path.exists(metadata_filepath):
    with open(metadata_filepath, "r") as m_f:
      metadata_contents = json.load(m_f)




  while how_many_msgs_to_send:
    if metadata_contents and shuffle_inputfile_if_reached_end:
        decayed_delay_trigger = DELAY_BETWEEN_TRIGGER * 0.9977777778
        regenerate_same_inputfile(metadata_contents["weightage_mapping"], input_file_path, metadata_contents["num_of_msgs_to_form"], metadata_contents["num_records_per_table"],metadata_contents["tables_template_file"])
        regeneration_count+=1
        logging.info(f"Metadata contents found.. so inputfile is regenerated. regeneration_count : {regeneration_count}")

    elif not shuffle_inputfile_if_reached_end:
        logging.info(f"Not regenerating inputfile because shuffle_inputfile_if_reached_end set to {shuffle_inputfile_if_reached_end}")
    else:
      logging.info(f"Not regenerating inputfile because Metadata contents not found.. so using same inputfile for next iteration.")

    with open(input_file_path) as fs:
        while how_many_msgs_to_send:
            current_msg = fs.readline().strip('\n')
            # Break if the end of the file is reached
            if not current_msg:
                logging.info("reached end of input file, breaking the loop")
                logging.info(datastats_action)
                logging.info(datastats)
                logging.info(f"record_count: {record_count}")
                break
            
            # unix_timestamp=int(time.time())
            unix_timestamp += DELAY_BETWEEN_TRIGGER
            final_message= str(unix_timestamp) + current_msg

            if len(final_message) > 50065000:
              logging.info(f"WARNING : length of msg exceeded 50065000, so skipping this msg")
              continue
            
            _thread.start_new_thread(analyse,(current_msg,))  # Analyze the current message
            
            _thread.start_new_thread(SendTrigger, (final_message,portlist))

            how_many_msgs_to_send -= 1
            logging.info(f"Msg sent!  {how_many_msgs_to_send} remaining, Timestamp : {unix_timestamp}")
            if how_many_msgs_to_send%51 == 0:
              logging.info(datastats_action)
            time.sleep(decayed_delay_trigger)

    iteration_count+=1
    logging.info(f"Iteration complete! iteration count is {iteration_count}")


logging.info("------------------------------")

elapsed_time = time.time() - start_time
total_analyse_time += elapsed_time
logging.info(f"Load completed in {total_analyse_time} seconds")

logging.info("------------------------------")

logging.info(f"Reached End of load, Remaining msgs to send : {how_many_msgs_to_send}")
if how_many_msgs_to_send!=0:
   logging.critical(f"how_many_msgs_to_send is not equal to zero : {how_many_msgs_to_send}")

logging.info("------------------------------")

logging.info("Analysing datastats_action dictionary ... ")
logging.info(datastats_action)

action_wise_count_result = {
    "added":0,
    "removed":0,
    "snapshot":0
}
total_datastats_action_count=0

for table in datastats_action:
    for key,val in datastats_action[table].items():
        action_wise_count_result[key] += val
        total_datastats_action_count+=val

logging.info(f"action_wise_count_result : {action_wise_count_result}")
logging.info(f"total_datastats_action_count : {total_datastats_action_count}")

logging.info("------------------------------")

logging.info("Analysing datastats dictionary ... ")
datastats_df  = pd.DataFrame(list(datastats.items()), columns=['table', 'count'])
datastats_df = datastats_df.sort_values(by=['count','table'], ascending=False)
logging.info("\n%s", datastats_df.to_string(index=False))
logging.info(datastats)
total_datastats_count = 0
for t,v in datastats.items():
    total_datastats_count+=v
logging.info(f"total_datastats_count : {total_datastats_count}")

logging.info("------------------------------")

logging.info(f"record_count: {record_count}")

logging.info("------------------------------")

logging.info(f"input file is iterated {iteration_count} times")
logging.info(f"input file is Regenerated {regeneration_count} times")

if record_count != total_datastats_action_count or record_count!=total_datastats_count or total_datastats_count!=total_datastats_action_count:
   logging.warning(f"records count if different dictionaries are not martching. record_count:{record_count}, total_datastats_count:{total_datastats_count}, total_datastats_action_count:{total_datastats_action_count}")

if metadata_contents:
    expected_sent_records ={table:val*iteration_count for table,val in  metadata_contents["count_of_records_for_each_table"].items()}
    if expected_sent_records == datastats:
        logging.info("Success : Expected number of records are sent.")
    elif saved_how_many_msgs_to_send % metadata_contents["num_of_msgs_to_form"] != 0:
        logging.warning("Provided 'how_many_msgs_to_send' should be multiple of no. of msgs in the inputfile if you want to calculate accuracies.")
    else:
        logging.critical("Number of sent records are not equal to expected number of records.")
