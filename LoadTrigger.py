import time
import sys
import datetime
import json
import logging
import _thread
import threading
import requests
from simulator_config_vars import testinput_file,INPUT_FILES_PATH, DELAY_BETWEEN_TRIGGER, TIME, INPUTFILES_METADATA_PATH, shuffle_inputfile_if_reached_end
import os
from GenerateInputFile import regenerate_same_inputfile

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
        #print("No of records : ",len(pydict['data']))
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
                

            # if datastats_action.get(table_name) == None:
            #     datastats_action[table_name]={"added":0,"removed":0,"snapshot":0}
            # if record.get('action') == 'added':
            #         datastats_action[table_name]['added'] +=1
            # if record.get('action') == 'removed':
            #         datastats_action[table_name]['removed'] +=1
            # if record.get('action') == 'snapshot':
            #         datastats_action[table_name]['snapshot'] +=1
            # if record.get('name') == None:
            #     print(("Warning ,name is missing in :",record))
            # if datastats.get(table_name) == None:
            #     datastats[table_name] = 1
            # else:
            #     datastats[table_name]+=1

def actual_send(msg,port):
      x = requests.post(f"http://{LOCAL_HOST}:"+str(port), data=msg)
      #print(dir(x))
      #print(x.status_code)
      #print(x.url)

def SendTrigger(msg,portlist):
    for Port in portlist:
      _thread.start_new_thread(actual_send, (msg,Port))

try:
   with open(testinput_file) as f:
      data = f.read()
      testinput_contents= json.loads(data)
except Exception as e:
    print(f"Error occured while processing  {testinput_file}",e)
    sys.exit(1)
    
all_instances=testinput_contents['instances']
# duration_of_load_in_sec = testinput_contents['duration_of_load_in_sec']
# how_many_msgs_to_send = duration_of_load_in_sec // DELAY_BETWEEN_TRIGGER

how_many_msgs_to_send = testinput_contents['how_many_msgs_to_send']

input_file_path = os.path.join(INPUT_FILES_PATH, testinput_contents['inputfile'])
if not os.path.isfile(input_file_path):
  print(f"Error: Input File '{input_file_path}' does not exist.")
  raise f"Error: Input File '{input_file_path}' does not exist."     


Time=TIME.split('-')
if Time[0] == '0000':
  unix_timestamp=int(time.time())
  print(f"year provided is {Time[0]}, new unix_timestamp generated is : ", unix_timestamp)
else:
  year,month,day,hr,minute=int(Time[0]),int(Time[1]),int(Time[2]),int(Time[3]),int(Time[4])
  datetime_object = datetime.datetime(year,month,day,hr,minute)
  unix_timestamp = int(time.mktime(datetime_object.timetuple()))
  print(f"year provided is {Time[0]}, so using provided unix_timestamp : ", unix_timestamp)

portlist=[]
for eachinstance in all_instances:
   portlist.append(eachinstance['port'])


file_name_without_suffix = os.path.splitext(os.path.basename(input_file_path))[0]
metadata_filepath = os.path.join(INPUTFILES_METADATA_PATH, file_name_without_suffix+".json")
print(metadata_filepath)

if os.path.exists(metadata_filepath):
  with open(metadata_filepath, "r") as m_f:
    metadata_contents = json.load(m_f)
else:
    metadata_contents = None

iteration_count = 1
total_analyse_time = 0
start_time = time.time()
while how_many_msgs_to_send:

  logging.info(f"Iterating inputfile... iteration count is {iteration_count}")
  if metadata_contents and shuffle_inputfile_if_reached_end:
    logging.info("Metadata contents found.. so regenerating inputfile.")
    regenerate_same_inputfile(metadata_contents["complete_collection_of_all_tables_occurences"], input_file_path, metadata_contents["num_of_msgs_to_form"], metadata_contents["num_records_per_table"])
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
          
          unix_timestamp=int(time.time())
          final_message= str(unix_timestamp) + current_msg

          if len(final_message) > 50065000:
            logging.info(f"WARNING : length of msg exceeded 50065000, so skipping this msg")
            continue
          
          _thread.start_new_thread(analyse,(current_msg,))  # Analyze the current message
          
          _thread.start_new_thread(SendTrigger, (final_message,portlist))

          how_many_msgs_to_send -= 1
          logging.info(f"Msg sent! {how_many_msgs_to_send} remaining, Timestamp : {unix_timestamp}")
          if how_many_msgs_to_send%51 == 0:
            logging.info(datastats_action)
          time.sleep(DELAY_BETWEEN_TRIGGER)

  iteration_count+=1

logging.info(f"Reached End of load, how_many_msgs_to_send:{how_many_msgs_to_send} ")
logging.info(datastats_action)
logging.info(datastats)
logging.info(f"record_count: {record_count}")
logging.info(f"input file is iterated {iteration_count} times")

elapsed_time = time.time() - start_time
total_analyse_time += elapsed_time
logging.info(total_analyse_time)