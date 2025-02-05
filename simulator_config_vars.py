import os
import subprocess
SSH_PORT = 22
ABACUS_USERNAME = 'abacus'  
ABACUS_PASSWORD = 'abacus' 
SIMULATOR_SERVER_PORT = 8123

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

STACK_JSONS_PATH = os.path.join(ROOT_PATH,'stacks')
SECRETS_JSONS_PATH = os.path.join(ROOT_PATH,'secrets')
TESTINPUT_FILES_PATH = os.path.join(ROOT_PATH,'testinput_json_files')
HOSTNAMES_FILES_PATH = os.path.join(ROOT_PATH,'hostnames')
INPUT_FILES_PATH = os.path.join(ROOT_PATH,'input_files')

hostname = subprocess.run("hostname",shell=True,capture_output=True,text=True).stdout.strip()
testinput_file = os.path.join(TESTINPUT_FILES_PATH,f"{hostname}_testinput.json")

unit_load_time_in_mins = 5
num_tables_per_msg = 6
num_records_per_table = 12
osquery_template_file = "tables_template.json"