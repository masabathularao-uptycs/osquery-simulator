import os
import subprocess
SSH_PORT = 22
ABACUS_USERNAME = 'abacus'  
ABACUS_PASSWORD = 'abacus' 

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

STACK_JSONS_PATH = os.path.join(ROOT_PATH,'stacks')
SECRETS_JSONS_PATH = os.path.join(ROOT_PATH,'secrets')
TESTINPUT_FILES_PATH = os.path.join(ROOT_PATH,'testinput_json_files')
HOSTNAMES_FILES_PATH = os.path.join(ROOT_PATH,'hostnames')
INPUT_FILES_PATH = os.path.join(ROOT_PATH,'input_files')

hostname = subprocess.run("hostname",shell=True,capture_output=True,text=True).stdout.strip()


TOTAL_NUMBER_OF_ASSETS =  10_000
NUM_CUSTOMERS = 100
stack_json_file = 's1_nodes.json'
first_x_customer_percentage=20
load_percentage_for_first_x_percent_customers=20

test_input_params={
    "time": "0000-01-02-01-01",
    "inputfile": f"{INPUT_FILES_PATH}/rhel7-6tab_12rec.log",
    "startline": 0,
    "endline": 600,
    "delaybetweentrigger": 4,
    "time_between_instance_seconds": 10,
    "message_multiplier": 2,
    "repeat_input_file": 0,
    "linenumber": 0,
    "numberoftriggers": 200
}

testinput_file = os.path.join(TESTINPUT_FILES_PATH,f"{hostname}_testinput.json")
