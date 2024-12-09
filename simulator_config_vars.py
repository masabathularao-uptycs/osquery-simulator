import os

SSH_PORT = 22
ABACUS_USERNAME = 'abacus'  
ABACUS_PASSWORD = 'abacus' 

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

STACK_JSONS_PATH = os.path.join(ROOT_PATH,'stacks')
SECRETS_JSONS_PATH = os.path.join(ROOT_PATH,'secrets')
TESTINPUT_FILES_PATH = os.path.join(ROOT_PATH,'/testinput_files')

TOTAL_NUMBER_OF_ASSETS =  10_000
LOAD_DURATION_IN_SECONDS = 600
LOAD_TYPE = "multicustomer"
NUMBER_OF_CUSTOMERS = 100