import paramiko,socket
from simulator_config_vars import SSH_PORT,ABACUS_PASSWORD,ABACUS_USERNAME
import subprocess

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

def execute_shell_command(command):
    try:
        result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.stderr.strip() == '':
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error executing command '{command}': {e}"