import os
import subprocess
SSH_PORT = 22
ABACUS_USERNAME = 'abacus'  
ABACUS_PASSWORD = 'abacus' 
SIMULATOR_SERVER_PORT = 8123

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

HOSTNAMES_FILES_PATH = os.path.join(ROOT_PATH,'hostnames')
INPUT_FILES_PATH = os.path.join(ROOT_PATH,'inputfiles')

hostname = subprocess.run("hostname",shell=True,capture_output=True,text=True).stdout.strip()
testinput_file = os.path.join(ROOT_PATH,"testinput.json")

unit_load_time_in_mins = 10
num_tables_per_msg = 6
num_records_per_table = 12


OSQUERY_TABLES_TEMPLATE_FILE = "tables_template.json"
DELAY_BETWEEN_TRIGGER = 4  #this means 1 msg is sent for every 4secodns => timetaken to send 150 msgs is 600sec(10mins)
TIME_BETWEEN_INSTANCE_ENROLLMENT = 10

TIME =  "0000-01-02-01-01"
shuffle_inputfile_if_reached_end = False