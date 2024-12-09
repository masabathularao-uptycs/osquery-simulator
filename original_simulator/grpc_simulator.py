import socket
import time
import sys
import datetime
import json
import logging
import _thread
import threading
import requests
import traceback
import os

global datastats_action
global statsflag
global linenumber

datastats_action={}
connections={}
sent_cons={}
statsflag=True
message_multiplier = 1

def set_tables():
    with open("table_types.json", "r", encoding = "utf-8") as fin:
        js = json.load(fin)
    to_return = {}
    for table in js["tables"]:
        name = table["name"]
        to_set = {}
        for col in table["columns"]:
            column_name = col["name"]
            tpe = col["type"]
            if tpe == "TEXT_TYPE":
                grpc_type = "str"
            elif tpe == "INTEGER_TYPE":
                grpc_type = "i32"
            elif tpe == "BIGINT_TYPE":
                grpc_type = "i64"
            else:
                grpc_type = "i64"
            to_set[column_name] = grpc_type
        if name == "process_open_sockets":
            to_return["process_open_sockets_local"] = to_set
            to_return["process_open_sockets_remote"] = to_set
        else:
            to_return[name] = to_set
    return to_return

schema = set_tables()

def get_cell_type(table_name, column):
    try:
        return schema[table_name][column]
    except:
        return "str"

def update_grpc_row(row):
  to_set = list()
  name = row["name"]
  for col in row["columns"]:
    to_set.append(get_cell_type(name, col))
  row["rows"] = row["rows"] * message_multiplier
  row["added"] = row["added"] * message_multiplier
  row["types"] = to_set

def make_result(grpc_row, unix_time):
    m = sim_pb2.ResultRequest()
    name = grpc_row["name"]
    m.name = name
    m.unix_time = unix_time
    m.epoch = int(time.time())
    m.counter = 1000
    m.snapshot = grpc_row["snapshot"]
    m.columns.extend(grpc_row["columns"])
    for outer,row in enumerate(grpc_row["rows"]):
        res = sim_pb2.ResultRequest.Result()
        res.removed = not(grpc_row["added"][outer])
        for index, val in enumerate(row):
            cell_type = get_cell_type(name, grpc_row["columns"][index])
            cell = sim_pb2.ResultRequest.Cell()
            if cell_type == "str":
                cell.str = val
            elif cell_type == "int32":
                cell.i32 = val
            else:
            #elif cell_type == "int64":
                cell.i64 = int(val)
            #else:
            #    cell.double = val
            res.cells.append(cell)
        m.results.append(res)
    return m


headers = {'Content-type': 'text/html'}

logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')

try:
  os.run('rm *.er_log >/dev/null 2>&1')
except:
  pass


def timeinlinux(ts):
  ts_sep=ts.split(" ")
  ts_date=ts_sep[0].split('-')
  ts_time=ts_sep[1].strip('\n').split(':')
  d=datetime.datetime(int(ts_date[0]),int(ts_date[1]),int(ts_date[2]),int(ts_time[0]),int(ts_time[1]),int(ts_time[2]))
  tstamp=time.mktime(d.timetuple())
  return tstamp

def statsdump():
    global linenumber
    global statsflag
    while statsflag:
      time.sleep(100)
      logging.warning(linenumber)
      logging.warning(datastats_action)


def analyse(line_json):
    for record in line_json:
        try:
            name = record["name"]
        except:
            print("Warning ,name is missing in :",record)
            return
        if datastats_action.get(name) == None:
            datastats_action[name]={"added":0,"removed":0,"snapshot":0}
        # is not a snapshot
        if record["snapshot"] == False:
            for added in record["added"]:
                if added:
                    datastats_action[name]['added'] =  datastats_action[name]['added'] + (1 * message_multiplier)
                if not(added):
                    datastats_action[name]['removed'] = datastats_action[name]['removed'] + (1 * message_multiplier)
        # is a snapshot
        else:
            num_records = len(record["added"])
            datastats_action[name]['snapshot'] = datastats_action[name]['snapshot'] + (num_records * message_multiplier)
    
    to_pop = list()
    for index,row in enumerate(line_json):
      if "upt_" in row["name"]:
        to_pop.append(index)
    to_pop.reverse()
    for index in to_pop:
      line_json.pop(index)
    for row in line_json:
      update_grpc_row(row)
 

def threaded_msg(port, url, data, count=0):
  try:
    persistent_con = connections[port]
    resp = persistent_con.post(url, data=data, headers=headers)
    sent_cons[port] += 1
    if resp.status_code != 200:
      er_log = open('%s.err' % (port), 'a+')
      er_log.write('non 200 status code with msg %s' % (resp.content))
      er_log.close()
  except Exception as e:
    er_log = open('%s.err' % (port), 'a+')
    er_log.write('error from post:  %s\n' % (e))
    er_log.close()
    if count < 5:
        time.sleep(3)
        threaded_msg(port, url, data, count=count+1)

 
def SendTrigger(sockudp,msg,destip,portlist,timefornexttrigger):
    inetrvaltime=float(timefornexttrigger)/float(len(portlist)) *0.70
    for Port in portlist:
        #sockudp.sendto(msg, (destip, Port))
        url = 'http://localhost:' + str(Port) + '/log_message'
        _thread.start_new_thread(threaded_msg, (Port, url, msg))
        time.sleep(inetrvaltime)


sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

t = threading.Timer(20.0, statsdump)
t.start()  # after 30 seconds, "hello, world" will be printed

UDP_IP = "127.0.0.1"
count=0
argvcount=sys.argv
print(argvcount)
if len(argvcount) != 2:
   print("Invalid arguments")
   print("python load_trigger.py testinput.json")
   sys.exit(1)
try:
   with open(argvcount[1]) as f:
      data = f.read()
except Exception:
    print("could not open file ",argvcount[1])
    sys.exit(1)
   #do something with data
try:
   loadinput= json.loads(data)
except Exception:
    print("conent of ",argvcount[1]," is not complying with json format")
instance=loadinput['instances']
endline=loadinput['endline']
message_multiplier = loadinput.get("message_multiplier",1)

portlist=[]
for eachinstance in instance:
   portlist.append(eachinstance['port'])
   connections[eachinstance['port']] = requests.session()
   sent_cons[eachinstance['port']] = 0
print(portlist)
linenumber=loadinput['linenumber']
trafficinstances=loadinput['trafficinstances']

if linenumber == 0:
    print("play full file")
    firstline=0
    linenumber=0
    TimeCon=loadinput['time']
    Time= TimeCon.split('-')
    if Time[0] == '0000':
      starttime=int(str(time.time()).split('.')[0])
    else:
      year=int(Time[0])
      month=int(Time[1])
      day=int(Time[2])
      hr=int(Time[3])
      minute=int(Time[4])
      d = datetime.datetime(year,month,day,hr,minute)
      starttime = int(time.mktime(d.timetuple()))

    
    diff_ts=0
    with open(loadinput['inputfile']) as fs:
      startline=loadinput['startline']
      if startline != 0:
        print('start skipping lines')
        logging.warning("skipping "+str(startline) +" lines")
        for Line in range(0,startline-1):
          linebuffer=fs.readline()
          linenumber=linenumber+1

        if len(linebuffer) < 30:
          linebuffer=fs.readline()
          linenumber=linenumber+1          
      while 1:
        if firstline == 0:
            first_ts=fs.readline()
            first_ts=timeinlinux(first_ts)
            firstline=1
            linenumber=linenumber+1
        grpc_row,second_ts=fs.readline(),fs.readline()

        grpc_row=grpc_row.strip('\n')
        grpc_row = json.loads(grpc_row)
        #print(grpc_row)
        linenumber=linenumber+2
        if len(grpc_row) == 0:
          break
        if len(second_ts) == 0:
          break
        second_ts=timeinlinux(second_ts)
        starttime=starttime+diff_ts
        starttimestr=str(starttime).split('.')[0]
        #not longer limiting strings to 65 KB
        if len(grpc_row) > 300000:
          continue
        analyse(grpc_row)
        #logging.warning("Line number : " +str(linenumber) + ',tstamp : ' + starttimestr)
        diff_ts=float(second_ts-first_ts)
        if diff_ts <= 0:
          diff_ts=4.0
        if abs(diff_ts) > 100:
          print(linenumber, "please check date at line ",linenumber, ' in json input')
          logging.warning("please check date at line "+ str(linenumber)+ ' in json input')
        diff_ts=4.0
        logging.warning("Line number : " +str(linenumber) + ',tstamp : ' + starttimestr + " len: " + str(len(str(grpc_row))))
        _thread.start_new_thread(SendTrigger, (sock, starttimestr + json.dumps(grpc_row),UDP_IP,portlist[0:trafficinstances],diff_ts))
        time.sleep(diff_ts)
        first_ts=second_ts
        if endline != 0:
           if endline <= linenumber:
              break
    statsflag=False      


    
else:
    print("play single log message")
    TimeCon=loadinput['time']
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
    with open(loadinput['inputfile']) as f:
      for Line in range(0,int(loadinput['linenumber'])):
          Con = f.readline().strip('\n')
    for no in range(0,int(loadinput['numberoftriggers'])):
     curtime=int(str(time.time()).split('.')[0]) 
     difftime=curtime-begtime
     newtime=unixtime+difftime
     TS=str(newtime).split('.')[0]
     print(TS)
     con=TS + Con
     count=count+1
     print(count,len(con))
    # do not limit by size anymore
     if len(con) > 300000:
       continue
     if len(con) == 10:
        print("reading data is done",count)
        break
     if loadinput['delaybetweentrigger'] == '0':
        delay=1
     else:
         delay=int(loadinput['delaybetweentrigger'])
     time.sleep(delay)
     analyse(Con)
     logging.warning("trigger no: " +str(no))
     for Port in portlist[0:trafficinstances]:
        sock.sendto(con, (UDP_IP, Port))
    statsflag=False      

logging.warning(datastats_action)

print(sent_cons)
