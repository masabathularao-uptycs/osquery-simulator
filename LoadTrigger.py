import time
import sys
import datetime
import os
import json
import logging
import _thread
import threading
import requests

global datastats_action
global record_count
global statsflag
global linenumber

record_count=0
datastats_action={}
datastats={}
statsflag=True

logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')

base_dir_path =os.path.dirname(os.path.realpath(__file__))
testinput_file = os.path.join(base_dir_path,"testinput.json")
LOCAL_HOST = "127.0.0.1"


def statsdump():
    global linenumber
    global statsflag
    while statsflag:
      time.sleep(100)
      logging.warning(linenumber)
      logging.warning(datastats_action)

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

thread_to_print_stats = threading.Timer(30.0, statsdump)
thread_to_print_stats.start()  

try:
   with open(testinput_file) as f:
      data = f.read()
      testinput_contents= json.loads(data)
except Exception as e:
    print(f"Error occured while processing  {testinput_file}",e)
    sys.exit(1)
    
instance=testinput_contents['instances']
endline=testinput_contents['endline']
delaybetweentrigger = testinput_contents['delaybetweentrigger']

print("Total duration of the load in seconds: ", endline*delaybetweentrigger/2)
portlist=[]
for eachinstance in instance:
   portlist.append(eachinstance['port'])

linenumber=testinput_contents['linenumber']

if linenumber == 0:
    print("playing full file...")
    firstline=0
    Time=testinput_contents['time'].split('-')
    if Time[0] == '0000':
      unix_timestamp=int(time.time())
      print(f"year provided is {Time[0]}, new unix_timestamp generated is : ", unix_timestamp)
    else:
      year,month,day,hr,minute=int(Time[0]),int(Time[1]),int(Time[2]),int(Time[3]),int(Time[4])
      datetime_object = datetime.datetime(year,month,day,hr,minute)
      unix_timestamp = int(time.mktime(datetime_object.timetuple()))
      print(f"year provided is {Time[0]}, so using provided unix_timestamp : ", unix_timestamp)

    with open(testinput_contents['inputfile']) as fs:
      startline=testinput_contents['startline']
      if startline != 0:
        print('start skipping lines')
        logging.warning("skipping "+str(startline) +" lines")
        for Line in range(0,startline-1):
          linebuffer=fs.readline()
          linenumber+=1

        if len(linebuffer) < 30:
          linebuffer=fs.readline()
          linenumber+=1
      if firstline == 0:
        first_ts=fs.readline()
        linenumber+=1

      while True:
        message,second_ts=fs.readline(),fs.readline()
        message=message.strip('\n')
        linenumber+=2
        if len(message)==0 or len(second_ts)== 0:break
        
        starttimestr=str(int(unix_timestamp+delaybetweentrigger))
        final_message=starttimestr + message

        if len(final_message) > 50065000:
          logging.warning("Line number : " +str(linenumber) + ',length of logger msg : ' + str(len(final_message)))
          continue
        logging.warning("Line number : " +str(linenumber) + ',tstamp : ' + starttimestr + ' ' + str(len(final_message)))
        analyse(message)
        _thread.start_new_thread(SendTrigger, (final_message,portlist))
        time.sleep(delaybetweentrigger)
        if endline != 0:
           if endline <= linenumber:
              break
        print("--------------")
    statsflag=False      


else:
    count=0
    print("play single log message")
    TimeCon=testinput_contents['time']
    Time= TimeCon.split('-')
    if Time[0] == '0000':
      unixtime=int(str(time.time()).split('.')[0])
    else:
      year=int(Time[0])
      month=int(Time[1])
      day=int(Time[2])
      hr=int(Time[3])
      minute=int(Time[4])
      d = datetime.datetime(year,month,day,hr,minute)
      unixtime = int(time.mktime(d.timetuple()))
    begtime=int(str(time.time()).split('.')[0])
    with open(testinput_contents['inputfile']) as f:
      for Line in range(0,int(testinput_contents['linenumber'])):
          message = f.readline().strip('\n')
    for no in range(0,int(testinput_contents['numberoftriggers'])):
     curtime=int(str(time.time()).split('.')[0]) 
     difftime=curtime-begtime
     newtime=unixtime+difftime
     TS=str(newtime).split('.')[0]
     print(TS)
     final_message=TS + message
     count=count+1
     print((count,len(final_message)))
     if len(final_message) > 65000:
        continue
     if len(final_message) == 10:
        print(("reading data is done",count))
        break
     if testinput_contents['delaybetweentrigger'] == '0':
        delay=1
     else:
         delay=int(testinput_contents['delaybetweentrigger'])
     time.sleep(delay)
     analyse(message)
     logging.warning("trigger no: " +str(no))
     for Port in portlist:
        _thread.start_new_thread(actual_send, (final_message,Port))
    statsflag=False
