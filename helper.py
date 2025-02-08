# import paramiko,socket
# from simulator_config_vars import SSH_PORT,ABACUS_PASSWORD,ABACUS_USERNAME
import subprocess

# def execute_command_in_node(node,command):
#     try:
#         print(f"Executing the command in node : {node}")
#         client = paramiko.SSHClient()
#         client.load_system_host_keys() 
#         client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#         try:
#             client.connect(node, SSH_PORT, ABACUS_USERNAME, ABACUS_PASSWORD)
#             stdin, stdout, stderr = client.exec_command(command)
#             out = stdout.read().decode('utf-8').strip()
#             errors = stderr.read().decode('utf-8')
#             if errors:
#                 print("Errors:")
#                 print(errors)
#             return out
                
#         except Exception as e:
#             print(e)
#             raise RuntimeError(f"ERROR : Unable to connect to {node} , {e}") from e
#         finally:
#             client.close()
#     except socket.gaierror as e:
#         print(e)
#         raise RuntimeError(f"ERROR : Unable to connect to {node} , {e}") from e
    
# def execute_configdb_query(node,query):
#     configdb_command = f'sudo docker exec postgres-configdb15 bash -c "PGPASSWORD=pguptycs psql -U postgres configdb -c \\"{query}\\""'
#     print(configdb_command)
#     return execute_command_in_node(node,configdb_command)

def execute_shell_command(command: str):
    """
    Executes a shell command and captures both the output and errors.

    Args:
        command (str): The shell command to execute.

    Returns:
        dict: A dictionary containing the command output, error (if any), and status.
    """
    try:
        # Run the command and capture both stdout and stderr
        result = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)
        return {
            "status": "success",
            "output": result.stdout.strip(),
            "error": None
        }
    except subprocess.CalledProcessError as e:
        # Handle errors when the command fails
        return {
            "status": "error",
            "output": e.stdout.strip(),
            "error": e.stderr.strip()
        }

# Example Usage
if __name__ == "__main__":
    command =  str(input()) # Replace with your shell command
    result = execute_shell_command(command)
    print("command:",command)
    print("result:",result)
    print("Status:", result["status"])
    print("Output:", result["output"])
    if result["error"]:
        print("Error:", result["error"])
