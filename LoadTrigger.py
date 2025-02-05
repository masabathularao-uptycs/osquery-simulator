import time
import sys
import datetime
import json
import logging
import _thread
import threading
import requests
from simulator_config_vars import testinput_file,INPUT_FILES_PATH, DELAY_BETWEEN_TRIGGER
from test_input_params import test_input_params
import os

global datastats_action
global record_count

record_count=0
datastats_action={}
datastats={}
statsflag=True

logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')

LOCAL_HOST = "127.0.0.1"

def analyse(message):
        global record_count
        pydict=json.loads(message)
        #print("No of records : ",len(pydict['data']))
        for record in pydict['data']:
            record_count +=1
            table_name = record['name']
            if datastats_action.get(table_name) == None:
                datastats_action[table_name]={"added":0,"removed":0,"snapshot":0}
            if record.get('action') == 'added':
                    datastats_action[table_name]['added'] +=1
            if record.get('action') == 'removed':
                    datastats_action[table_name]['removed'] +=1
            if record.get('action') == 'snapshot':
                    datastats_action[table_name]['snapshot'] +=1
            if record.get('name') == None:
                print(("Warning ,name is missing in :",record))
            if datastats.get(table_name) == None:
                datastats[table_name] = 1
            else:
                datastats[table_name]+=1

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
# duration_of_load_in_sec = test_input_params['duration_of_load_in_sec']
# how_many_msgs_to_send = duration_of_load_in_sec // DELAY_BETWEEN_TRIGGER

how_many_msgs_to_send = test_input_params['how_many_msgs_to_send']

input_file_path = os.path.join(INPUT_FILES_PATH, test_input_params['inputfile'])
if not os.path.isfile(input_file_path):
  print(f"Error: Input File '{input_file_path}' does not exist.")
  raise f"Error: Input File '{input_file_path}' does not exist."     


Time=test_input_params['time'].split('-')
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

iteration_count = 1
while how_many_msgs_to_send:
  print(f"Iterating inputfile ... , iteration count is {iteration_count}")
  with open(input_file_path) as fs:
      while how_many_msgs_to_send:
          current_msg = fs.readline().strip('\n')
          # Break if the end of the file is reached
          if not current_msg:
              logging.warning("reached end of input file, breaking the loop")
              break
          
          unix_timestamp+=DELAY_BETWEEN_TRIGGER
          final_message= str(int(unix_timestamp)) + current_msg

          logging.warning(f"msgs remaining to send : {how_many_msgs_to_send}, timestamp : {unix_timestamp}, length of logger msgs : {str(len(final_message))}")
          if len(final_message) > 50065000:
            logging.warning(f"WARNING : length of msg exceeded 50065000, so skipping this msg")
            continue
          
          analyse(current_msg)
          _thread.start_new_thread(SendTrigger, (final_message,portlist))
          # print(current_msg[:10])  # Process the line if needed
          how_many_msgs_to_send -= 1
          if how_many_msgs_to_send%20 == 0:
            logging.warning(datastats_action)
          time.sleep(DELAY_BETWEEN_TRIGGER)

logging.warning(f"Reached End of load, how_many_msgs_to_send:{how_many_msgs_to_send} ")
logging.warning(datastats_action)
logging.warning(datastats)
logging.warning(f"input file is iterated {iteration_count} times")