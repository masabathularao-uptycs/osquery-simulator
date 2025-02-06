import json
import sys
import subprocess
from simulator_config_vars import ROOT_PATH,HOSTNAMES_FILES_PATH,testinput_file, TIME_BETWEEN_INSTANCE_ENROLLMENT
from create_hostnames import generate  
import os

os.makedirs(HOSTNAMES_FILES_PATH,exist_ok=True)
generate(testinput_file)

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
   
   loadcmd=f'nohup {ROOT_PATH}/endpointsim --count=' + str(eachinstance['clients']) + ' --domain=' + eachinstance['domain'] +' --secret=' + '\'' + eachinstance['secret'] + '\'' + f' --name=\'{HOSTNAMES_FILES_PATH}/'+eachinstance['names'] + '\'' + ' --port=' +str(eachinstance['port']) + ' &> osx_log' + str(eachinstance['port']) +'.out &'
   #commands.getoutput(loadcmd)
   return loadcmd

def check_instance_state():
   #getting the ports from all the instances
   for eachinstance in instance_list:
      portlist.append(int(eachinstance['port']))

   for _ in range(10):
      cmd="sudo netstat -tanup | grep endpointsim | grep LISTEN |  wc -l"
      instance_up_count=subprocess.getoutput(cmd)
      if(int(instance_up_count)==num_expected_instances):
         break
      Fd1=open(f'{ROOT_PATH}/checkExecuteLoad.sh',"w")
      Fd1.write('#!/bin/bash' + '\n')

      #checking each instance whether they are up or not
      for eachinstance in instance_list:
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
      subprocess.getoutput(f'{ROOT_PATH}/checkExecuteLoad.sh')


try:
   with open(testinput_file) as f:
      data = f.read()
      testinput_contents= json.loads(data)
except Exception as e:
    print(f"Error occured while processing  {testinput_file}",e)
    sys.exit(1)

instance_list=testinput_contents['instances']
num_expected_instances = len(instance_list)

Fd=open(f'{ROOT_PATH}/executeload.sh',"w")
Fd.write('#!/bin/bash' + '\n')

for eachinstance in instance_list:
   loadcmd=f'nohup {ROOT_PATH}/endpointsim --count=' + str(eachinstance['clients']) + ' --domain=' + eachinstance['domain'] +' --secret=' + '\'' + eachinstance['secret'] + '\'' + f' --name=\'{HOSTNAMES_FILES_PATH}/'+eachinstance['names'] + '\'' + ' --port=' +str(eachinstance['port']) + ' &> osx_log' + str(eachinstance['port']) +'.out &'
   print(loadcmd)
   Fd.write(loadcmd +'\n')
   # Fd.write("sleep 10" +'\n')
   Fd.write("sleep " + str(TIME_BETWEEN_INSTANCE_ENROLLMENT) +'\n')
Fd.write("sleep 20" +'\n')   
Fd.close()
subprocess.getoutput("chmod 777 executeload.sh")
subprocess.getoutput(f'{ROOT_PATH}/executeload.sh')
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

