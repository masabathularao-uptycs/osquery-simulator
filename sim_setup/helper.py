import socket,paramiko

def execute_command_in_node(node,command):
    try:
        print(f"Executing the command in node : {node}")
        client = paramiko.SSHClient()
        client.load_system_host_keys() 
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(node,22, "abacus", "abacus")
            stdin, stdout, stderr = client.exec_command(command)
            out = stdout.read().decode('utf-8').strip()
            errors = stderr.read().decode('utf-8')
            if errors:
                print("Errors:")
                print(errors)
            return out
                
        except Exception as e:
            raise RuntimeError(f"ERROR : Unable to connect to {node} , {e}") from e
        finally:
            client.close()
    except socket.gaierror as e:
        raise RuntimeError(f"ERROR : Unable to connect to {node} , {e}") from e
    

def run_commands(testinput_base_path,sims,update_params,testinput_path,main_node,original_testinput_path):
    base_command = """for i in {} ;do ssh abacus@$i "hostname;cd {}/;{};exit";done"""

    current_values=f"""cat {testinput_path} | grep 'clients\|inputfile\|endline'"""
    current_values_complete_command = base_command.format(' '.join(sims),testinput_base_path,current_values)
    print(current_values_complete_command)

    print("Values before update")
    before_op = execute_command_in_node(main_node,current_values_complete_command)
    print(before_op)

    
    
    inp = input(f"Update sims with these values? {update_params} ? (y/n)")

    if inp == "y":
        if original_testinput_path:
            copy_original_testinput = f"cp {original_testinput_path} {testinput_path}"
            copy_original_testinput_command = base_command.format(' '.join(sims),testinput_base_path,copy_original_testinput)
            print(copy_original_testinput_command)
            execute_command_in_node(main_node,copy_original_testinput_command)

        for key,val in update_params.items():
            if type(val)==str:
                val = '\\"'+val+'\\"'
            command = f"""sed -i 's/\\"{key}\\":.*/\\"{key}\\": {val},/g' \\"{testinput_path}\\" """
            complete_command = base_command.format(' '.join(sims),testinput_base_path,command)
            print(complete_command)
            execute_command_in_node(main_node,complete_command)

            print()

        print("Values after update")
        after_op = execute_command_in_node(main_node,current_values_complete_command)
        print(after_op)
    else:
        print("Not updated")
