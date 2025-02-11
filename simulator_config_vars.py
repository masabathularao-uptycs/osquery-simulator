import os
import subprocess
SSH_PORT = 22
ABACUS_USERNAME = 'abacus'  
ABACUS_PASSWORD = 'abacus' 
SIMULATOR_SERVER_PORT = 8123

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

HOSTNAMES_FILES_PATH = os.path.join(ROOT_PATH,'hostnames')
INPUT_FILES_PATH = os.path.join(ROOT_PATH,'inputfiles')
INPUTFILES_METADATA_PATH = os.path.join(ROOT_PATH,'inputfiles_metadata')

hostname = subprocess.run("hostname",shell=True,capture_output=True,text=True).stdout.strip()
testinput_file = os.path.join(ROOT_PATH,"testinput.json")

NUMBER_OF_MSGS_PER_INPUTFILE = 150
DELAY_BETWEEN_TRIGGER = 4  #this means 1 msg is sent for every 4secodns => timetaken to send 150 msgs is 600sec(10mins)
# therefore , an input file (with 150 msgs, and sending each msg every 4 seconds), has unit load time of 10 mins.
DELAY_DECAY_FACTOR = 0.9975
# Calculation
calculated_unit_load_time_in_mins = NUMBER_OF_MSGS_PER_INPUTFILE * DELAY_BETWEEN_TRIGGER / 60

# Store as integer if perfect integer, else float
if calculated_unit_load_time_in_mins.is_integer():
    calculated_unit_load_time_in_mins = int(calculated_unit_load_time_in_mins)
else:
    calculated_unit_load_time_in_mins = float(calculated_unit_load_time_in_mins)

# print(calculated_unit_load_time_in_mins)

FIRST_X_PERCENT_TABLES = 30
GETS_Y_PERCENT_WEIGHTAGE = 60

NUMBER_OF_TABLES_PER_MSG = 6
NUMBER_OF_RECORDS_PER_TABLE = 12


OSQUERY_TABLES_TEMPLATE_FILE = os.path.join(ROOT_PATH,'tables_template.json')
OSQUERY_TABLES_IMPORTACE_ORDER = os.path.join(ROOT_PATH,'tables_importance_order_according_to_prod.csv')

TIME_BETWEEN_INSTANCE_ENROLLMENT = 20

TIME =  "0000-01-02-01-01"
shuffle_inputfile_if_reached_end = True