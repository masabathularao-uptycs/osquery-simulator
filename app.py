from flask import Flask, request, jsonify
import os
from simulator_config_vars import SIMULATOR_SERVER_PORT,STACK_JSONS_PATH,hostname,testinput_file, DELAY_BETWEEN_TRIGGER ,INPUT_FILES_PATH
from test_input_params import test_input_params
# from flask_session import Session 
import json
from CreateTestinputFiles import create_testinput_files
from helper import execute_shell_command

app = Flask(__name__)
# app.config['SECRET_KEY'] = '343c855017e725321cb7f35b89c98b9e'
# app.config['SESSION_TYPE'] = 'filesystem'
# Session(app)

OSQUERY_DATA_LOAD_NAMES = ["multicustomer","singlecustomer"]
OSQUERY_CONTROLPLANE_LOAD_NAMES = ["controlplane"]

@app.route('/get_osquery_simulator_names', methods=['GET'])
def get_osquery_simulator_names():
    # Get the 'name' parameter from the request
    stack_json_file_name = request.args.get('stack_json_file_name')
    loadname = request.args.get('loadname', '').lower()

    if loadname not in OSQUERY_DATA_LOAD_NAMES + OSQUERY_CONTROLPLANE_LOAD_NAMES:
        return jsonify({"status": "error","message": f"'loadname' should be in {OSQUERY_CONTROLPLANE_LOAD_NAMES} or {OSQUERY_DATA_LOAD_NAMES}."}), 400  # Bad Request

    # Validate the stack_json_file_path
    stack_json_file_path = os.path.join(STACK_JSONS_PATH, stack_json_file_name)
    if not os.path.exists(stack_json_file_path):
        return jsonify({"status": "error","message": f"The file '{stack_json_file_path}' does not exist."}), 404  # Not Found

    try:
        # Read and load the JSON file
        with open(stack_json_file_path, 'r') as json_file:
            json_data = json.load(json_file)

        # Fetch simulator data based on the loadname
        if loadname in OSQUERY_DATA_LOAD_NAMES:
            try:
                return_sims = json_data["osquery_data_load_params"]["sims"]
            except KeyError as e:
                return jsonify({"status": "error","message": f"The key 'osquery_data_load_params.sims' is missing in '{stack_json_file_path}': {e}"}), 500  # Internal Server Error

        elif loadname in OSQUERY_CONTROLPLANE_LOAD_NAMES:
            try:
                return_sims = json_data["osquery_controlplane_load_params"]["sims"]
            except KeyError as e:
                return jsonify({"status": "error","message": f"The key 'osquery_controlplane_load_params.sims' is missing in '{stack_json_file_path}': {e}"}), 500  # Internal Server Error
        else:
            return_sims = []

        # Return the fetched simulator list
        return jsonify({
            "status": "success",
            "message": f"Successfully fetched the simulator list for {stack_json_file_name} - {loadname} load",
            "result_data": return_sims,
            "input_files": os.listdir(INPUT_FILES_PATH)
        }), 200  # OK

    except json.JSONDecodeError as e:
        return jsonify({"status": "error","message": f"Failed to parse JSON from '{stack_json_file_path}': {e}"}), 400  # Bad Request

    except Exception as e:
        return jsonify({"status": "error","message": f"An unexpected error occurred: {e}"}), 500  # Internal Server Error

@app.route('/execute_shell_com', methods=['GET'])
def execute_shell_com():
    try:
        command = request.args.get('shell_command', '')
        result = execute_shell_command(command)
        return jsonify({"status": "success","message": f"Successfully executed {command} command on {hostname}","result":result}), 200  # Internal Server Error

    except Exception as e:
        return jsonify({"status": "error","message": f"An unexpected error occurred: {e}",}), 500  # Internal Server Error


@app.route('/check_sim_health', methods=['GET'])
def check_sim_health():
    bash_commands = {
        "endpointsim": "ps -ef | grep endpointsim | grep domain | grep secret | grep -v grep -c",
        "node": "ps -ef | grep node | grep domain | grep secret | grep -v grep -c",
        "LoadTrigger": "ps -ef | grep 'simulator/LoadTrigger.py' | grep -v grep -c",
        "load_running_since_sec": "ps -eo etimes,cmd | grep 'simulator/LoadTrigger.py' | grep -v grep | awk '{print $1}' | sort -n | head -n 1",

    }
    command_outputs = {}

    try:
        testinput_result = {}
        expected_instances = 0
        expected_assets = 0
        if os.path.exists(testinput_file):
            try:
                with open(testinput_file, 'r') as json_file:
                    testinput_file_contents = json.load(json_file)
                instances = testinput_file_contents["instances"]
                for instance in instances:
                    expected_instances+=1
                    expected_assets+=instance["clients"]
                    if instance["domain"] in testinput_result:
                        testinput_result[instance["domain"]] += instance["clients"]
                    else:
                        testinput_result[instance["domain"]] = instance["clients"]
            except Exception as e:
                print(f"Error while processing {testinput_file} contents")
        # Execute each bash command and collect the output
        for sim_type, command in bash_commands.items():
            command_outputs[sim_type] = execute_shell_command(command)
        try:
            load_dur_in_sec = int(test_input_params["how_many_msgs_to_send"])*DELAY_BETWEEN_TRIGGER
            hours = load_dur_in_sec // 3600
            minutes = (load_dur_in_sec % 3600) // 60
            remaining_seconds = load_dur_in_sec % 60

            main_params = [
                ("live instances", command_outputs.get("endpointsim", "endpointsim key not found in command_outputs dict")),
                ("exp. instances", expected_instances),
                ("assets to enroll", expected_assets),
                ("msgs to send", test_input_params.get("how_many_msgs_to_send", "how_many_msgs_to_send key not found in test_input_params dict")),
                ("load duration", f"{hours:02}:{minutes:02}:{remaining_seconds:02}"),
                ("inputfile", test_input_params.get("inputfile", "inputfile key not found in test_input_params dict")),
            ]
        except Exception as e:
            print(f"key not found error while creating main_params dictionary: {e}")
            main_params={}
        # Success response with command outputs
        try:
            remaining_load_duration = int(test_input_params["endline"]*2) - int(command_outputs["load_running_since_sec"])
        except:
            remaining_load_duration=0
    
        return jsonify({
            "status": "success",
            "message": f"Successfully fetched {hostname} health information.",
            "table_data_result":{
                "process_instances": command_outputs,
                "domain_count":testinput_result,
                "parameter_value":test_input_params
            },
            "main_params":main_params,
            "load_remaining_dur_in_sec":remaining_load_duration
        }), 200  # OK

    except Exception as e:
        return jsonify({"status": "error","message": f"An unexpected error occurred while checking health of {hostname}: {e}",}), 500  # Internal Server Error


@app.route('/update_load_params', methods=['POST'])
def update_load_params():
    try:
        # Get the incoming form data
        updated_params = request.form.to_dict()
        only_for_validation = updated_params.get("only_for_validation",False)
        print(not only_for_validation)
        if not updated_params:
            return jsonify({"status": "error","message": "No formdata is provided to update."}), 400  # Bad Request

        # Dynamically cast and validate the input
        for key, value in updated_params.items():
            if key in test_input_params:
                try:
                    # Determine the type of the current value in test_input_params
                    current_type = type(test_input_params[key])

                    # Cast the incoming value to the type of the existing value
                    if current_type is int:
                        updated_params[key] = int(value)
                    elif current_type is float:
                        updated_params[key] = float(value)
                    elif current_type is bool:
                        updated_params[key] = value.lower() in ['true', '1', 'yes']
                    else:
                        updated_params[key] = value  # Keep as string if not a recognized type
                except ValueError as e:
                    # Log and ignore type conversion errors
                    print(f"Invalid value for key '{key}': expected {current_type.__name__}." , e)

        
        # Call the function with updated parameters
        try:
            if "stack_json_file" not in test_input_params:
                return jsonify({"status": "error","message": f"Missing required key: 'stack_json_file' not present in test_input_params"}), 400  # Bad Request
            return_dict = create_testinput_files(updated_params,do_update=not only_for_validation)
            
            if not only_for_validation:
                # Update the global dictionary
                test_input_params.update(updated_params)
                    
                try:
                    # Save the updated dictionary back to the Python file
                    with open("test_input_params.py", 'w') as f:
                        f.write("test_input_params = " + json.dumps(test_input_params, indent=4))
                except (IOError, OSError) as file_error:
                    return jsonify({"status": "error","message": f"Failed to write to file: {str(file_error)}"}), 500  # Internal Server Error

                return jsonify({"status": "success","message": f"Parameters for {hostname} updated successfully. Please click on refresh button to view latest simulator parameters"}), 200  # OK
            else:
                return jsonify({"status": "success","message": f"Asset distribution logic calculated." , "asset_dist_data":return_dict}), 200  # OK

        except Exception as e:
            return jsonify({"status": "error","message": f"Error while calling create_testinput_files(): {str(e)}"}), 500  # Internal Server Error


    except Exception as e:
        return jsonify({"status": "error","message": f"An unexpected error occurred: {str(e)}"}), 500  # Internal Server Error




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=SIMULATOR_SERVER_PORT,debug=True)
