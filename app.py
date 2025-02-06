from flask import Flask, request, jsonify
import os
from simulator_config_vars import SIMULATOR_SERVER_PORT,hostname,testinput_file, DELAY_BETWEEN_TRIGGER ,INPUT_FILES_PATH
# from flask_session import Session 
import json
from helper import execute_shell_command

app = Flask(__name__)
# app.config['SECRET_KEY'] = '343c855017e725321cb7f35b89c98b9e'
# app.config['SESSION_TYPE'] = 'filesystem'
# Session(app)



@app.route('/execute_shell_com', methods=['GET'])
def execute_shell_com():
    try:
        command = request.args.get('shell_command', '')
        result = execute_shell_command(command)
        return jsonify({"status": "success","message": f"Successfully executed {command} command on {hostname}","result":result}), 200  # Internal Server Error

    except Exception as e:
        return jsonify({"status": "error","message": f"An unexpected error occurred: {e}",}), 500  # Internal Server Error

@app.route('/get_input_files', methods=['GET'])
def get_input_files():
    return jsonify({
            "status": "success",
            "message": f"Successfully fetched the inputfiles list from {hostname}",
            "input_files": os.listdir(INPUT_FILES_PATH)
        }), 200  # OK

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
        domain_and_count = {}
        expected_instances = 0
        expected_assets = 0
        if os.path.exists(testinput_file):
            try:
                with open(testinput_file, 'r') as json_file:
                    testinput_file_contents = json.load(json_file)
                instances = testinput_file_contents.pop("instances")
                for instance in instances:
                    expected_instances+=1
                    expected_assets+=instance["clients"]
                    if instance["domain"] in domain_and_count:
                        domain_and_count[instance["domain"]] += instance["clients"]
                    else:
                        domain_and_count[instance["domain"]] = instance["clients"]
            except Exception as e:
                print(f"Error while processing {testinput_file} contents")
        # Execute each bash command and collect the output
        for sim_type, command in bash_commands.items():
            command_outputs[sim_type] = execute_shell_command(command)
        try:
            load_dur_in_sec = int(testinput_file_contents["how_many_msgs_to_send"])*DELAY_BETWEEN_TRIGGER
            hours = load_dur_in_sec // 3600
            minutes = (load_dur_in_sec % 3600) // 60
            remaining_seconds = load_dur_in_sec % 60

            main_params = [
                ("live instances", command_outputs.get("endpointsim", "endpointsim key not found in command_outputs dict")),
                ("exp. instances", expected_instances),
                ("assets to enroll", expected_assets),
                ("msgs to send", testinput_file_contents.get("how_many_msgs_to_send", "how_many_msgs_to_send key not found in testinput_file_contents dict")),
                ("load duration", f"{hours:02}:{minutes:02}:{remaining_seconds:02}"),
                ("inputfile", testinput_file_contents.get("inputfile", "inputfile key not found in testinput_file_contents dict")),
            ]
        except Exception as e:
            print(f"key not found error while creating main_params dictionary: {e}")
            main_params={}
        # Success response with command outputs
        try:
            remaining_load_duration = int(testinput_file_contents["how_many_msgs_to_send"]*DELAY_BETWEEN_TRIGGER) - int(command_outputs["load_running_since_sec"])
        except:
            remaining_load_duration=0
    
        return jsonify({
            "status": "success",
            "message": f"Successfully fetched {hostname} health information.",
            "table_data_result":{
                "process_instances": command_outputs,
                "domain_count":domain_and_count,
                "parameter_value":testinput_file_contents
            },
            "main_params":main_params,
            "load_remaining_dur_in_sec":remaining_load_duration
        }), 200  # OK

    except Exception as e:
        return jsonify({"status": "error","message": f"An unexpected error occurred while checking health of {hostname}: {e}",}), 500  # Internal Server Error


@app.route('/update_load_params', methods=['POST'])
def update_load_params():
    try:
        updated_params = request.get_json()
        print(updated_params)

        if "instances" not in updated_params:
            return jsonify({"status": "error","message": f"Missing required key: 'instances' not present in received updated_params"}), 400  # Bad Request        
        try:
            # Save the updated dictionary back to the Python file
            with open(testinput_file, 'w') as f:
                f.write(json.dumps(updated_params, indent=4))
        except Exception as e:
            return jsonify({"status": "error","message": f"Failed to write to file: {str(e)}"}), 500  # Internal Server Error

        return jsonify({"status": "success","message": f"Parameters for {hostname} updated successfully. Please click on refresh button to view latest simulator parameters"}), 200  # OK


    except Exception as e:
        return jsonify({"status": "error","message": f"An unexpected error occurred: {str(e)}"}), 500  # Internal Server Error




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=SIMULATOR_SERVER_PORT,debug=True)
