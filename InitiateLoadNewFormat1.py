import json
import sys
import os
import time
import subprocess

from create_hostnames import generate

generate()

portlist=[]

def newport(eachinstance):

   #killing old port process 
   cmd="kill $(ps -ax | grep endpointsim | grep  {0} |  awk '{{print $1}}')".format(str(eachinstance['port']))
   subprocess.getoutput(cmd)

   #assigning  another port
   print("finding new port")
   newport=max(portlist)+1
   print(newport)
   #updating port in testinput.json
   cmdt="sed -i 's/{0}/{1}/g' testinput.json".format(str(eachinstance['port']),str(newport))
   subprocess.getoutput(cmdt)

   #updating port in instance and portlist
   portlist.remove(eachinstance['port'])
   eachinstance['port']=newport
   portlist.append(eachinstance['port'])
   
   loadcmd='nohup /home/abacus/go_http/endpointsim --count=' + str(eachinstance['clients']) + ' --domain=' + eachinstance['domain'] +' --secret=' + '\'' + eachinstance['secret'] + '\'' + ' --name=\'/home/abacus/go_http/'+eachinstance['names'] + '\'' + ' --port=' +str(eachinstance['port']) + ' &> osx_log' + str(eachinstance['port']) +'.out &'
   #commands.getoutput(loadcmd)
   return loadcmd

def check_instance_state():
   #getting the ports from all the instances
   for eachinstance in instance:
      portlist.append(int(eachinstance['port']))
   i=0
   while(i<10):
      i=i+1
      print(("while loop" ,i))
      cmd="sudo netstat -tanup | grep endpointsim | grep LISTEN |  wc -l"
      instance_up_count=subprocess.getoutput(cmd)
      if(int(instance_up_count)==len(instance)):
         break
      Fd1=open('/home/abacus/go_http/checkExecuteLoad.sh',"w")
      Fd1.write('#!/bin/bash' + '\n')
      #checking each instance whether they are up or not
      for eachinstance in instance:
         port=eachinstance['port']
         cmd="sudo netstat -tanup | grep endpointsim | grep LISTEN | grep  {0} | wc -l".format(str(eachinstance['port']))
         status=subprocess.getoutput(cmd)
         #status is 1 ,if it is up and 0 ,if it is down 
         if status=="1":
            continue
         else:
            #calling below function to up the instance again with different port 
            #print(eachinstance['port'])
            #print("status" ,status)
            loadcmd=newport(eachinstance)
            Fd1.write(loadcmd +'\n')
            Fd1.write("sleep 10" +'\n')
      Fd1.write("sleep 20" +'\n')      
      Fd1.close()
      subprocess.getoutput("chmod 777 checkExecuteLoad.sh")
      subprocess.getoutput("/home/abacus/go_http/checkExecuteLoad.sh")



argvcount=sys.argv
print(argvcount)
if len(argvcount) != 2:
   print("Invalid arguments")
   print("python InitiateLoad.py testinput.json")
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
   #print loadinput
except Exception:
    print("conent of ",argvcount[1]," is not complying with json format")

instance=loadinput['instances']
print("number of instances",len(instance))
print('-------------------------------')
#print instance
print('-------------------------------')
Fd=open('/home/abacus/go_http/executeload.sh',"w")
Fd.write('#!/bin/bash' + '\n')
instancecmd=[]
for eachinstance in instance:
   loadcmd='nohup /home/abacus/go_http/endpointsim --count=' + str(eachinstance['clients']) + ' --domain=' + eachinstance['domain'] +' --secret=' + '\'' + eachinstance['secret'] + '\'' + ' --name=\'/home/abacus/go_http/'+eachinstance['names'] + '\'' + ' --port=' +str(eachinstance['port']) + ' &> osx_log' + str(eachinstance['port']) +'.out &'
   instancecmd.append(loadcmd)
   print(loadcmd)
   Fd.write(loadcmd +'\n')
   Fd.write("sleep 10" +'\n')
   #Fd.write("sleep " + str(loadinput["time_between_instance_seconds"]) +'\n')
Fd.write("sleep 20" +'\n')   
Fd.close()
subprocess.getoutput("chmod 777 executeload.sh")
subprocess.getoutput("/home/abacus/go_http/executeload.sh")
check_instance_state()



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

