import json
import sys
import os
import time
import commands

argvcount=sys.argv
print argvcount
if len(argvcount) != 2:
   print "Invalid arguments"
   print "python InitiateLoad.py testinput.json"
   sys.exit(1)
try:
   with open(argvcount[1]) as f:
      data = f.read()
except Exception:
    print "could not open file ",argvcount[1]
    sys.exit(1)
   #do something with data
try:
   loadinput= json.loads(data)
   #print loadinput
except Exception:
    print "conent of ",argvcount[1]," is not complying with json format"

instance=loadinput['instances']
print "number of instances",len(instance)
print '-------------------------------'
#print instance
print '-------------------------------'
Fd=open('/home/abacus/go_http/executeload.sh',"w")
Fd.write('#!/bin/bash' + '\n')
instancecmd=[]
for eachinstance in instance:
   loadcmd='nohup /home/abacus/go_http/endpointsim --count=' + str(eachinstance['clients']) + ' --domain=' + eachinstance['domain'] +' --secret=' + '\'' + eachinstance['secret'] + '\'' + ' --name=\'/home/abacus/go_http/'+eachinstance['names'] + '\'' + ' --port=' +str(eachinstance['port']) + ' &> osx_log' + str(eachinstance['port']) +'.out &'
   instancecmd.append(loadcmd)
   print loadcmd
   Fd.write(loadcmd +'\n')
   Fd.write("sleep 6" +'\n')
   #Fd.write("sleep " + str(loadinput["time_between_instance_seconds"]) +'\n')
Fd.close()
commands.getoutput("chmod 777 executeload.sh")
commands.getoutput("/home/abacus/go_http/executeload.sh")

#def kill_process_by_port(port):
#    res = commands.getoutput("ps -aef | grep endpointsim | grep %s | awk '{ print $2 }'" % (port)
#    if 

# check if the port truly came up
#def try_other_port(port):
#    # kill old port
#    kill_process_by_port(port)

#for inst in instance:
#    port = inst["port"]
#    cmd = "netstat -an | grep %s | grep LISTEN | wc -l" % (port)
#    res = commands.getoutput(cmd)
#    if int(res) == 1:
#        continue
#    else:
#        try_other_port(port)
