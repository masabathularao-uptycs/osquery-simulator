import paramiko,socket
from simulator_config_vars import *
import json

def execute_command_in_node(node,command):
    try:
        print(f"Executing the command in node : {node}")
        client = paramiko.SSHClient()
        client.load_system_host_keys() 
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(node, SSH_PORT, ABACUS_USERNAME, ABACUS_PASSWORD)
            stdin, stdout, stderr = client.exec_command(command)
            out = stdout.read().decode('utf-8').strip()
            errors = stderr.read().decode('utf-8')
            if errors:
                print("Errors:")
                print(errors)
            return out
                
        except Exception as e:
            print(e)
            raise RuntimeError(f"ERROR : Unable to connect to {node} , {e}") from e
        finally:
            client.close()
    except socket.gaierror as e:
        print(e)
        raise RuntimeError(f"ERROR : Unable to connect to {node} , {e}") from e
    
def execute_configdb_query(node,query):
    configdb_command = f'sudo docker exec postgres-configdb15 bash -c "PGPASSWORD=pguptycs psql -U postgres configdb -c \\"{query}\\""'
    print(configdb_command)
    return execute_command_in_node(node,configdb_command)

def collect_secretkeys(configdb_node, base_domain):
    query = f"select domain,secret from customers"
    output = execute_configdb_query(configdb_node, query)
    # Step 1: Process the lines
    lines = output.splitlines()

    # Step 2: Filter out the lines that don't contain data
    data_lines = [line for line in lines if '|' in line and not line.startswith('-')]
    # Step 3: Extract key-value pairs
    data_dict = {}
    for line in data_lines:
        if "|" in line:
            try:
                domain, secret = map(str.strip, line.split('|'))
                data_dict[domain] = secret
            except ValueError as ve:
                print(f"Error parsing line: {line} -> {ve}")

    # Step 4: Save the dictionary to a JSON file
    try:
        filepath = f"{SECRETS_JSONS_PATH}/{base_domain}.json"
        print(f"Saving to: {filepath}")
        with open(filepath, 'w') as f:
            json.dump(data_dict, f, indent=4)
        print("Data saved to JSON file:", filepath)
    except Exception as e:
        print(f"Error writing to JSON file: {e}")

   