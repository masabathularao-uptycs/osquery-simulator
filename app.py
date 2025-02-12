from flask import Flask, request, jsonify
import os
from simulator_config_vars import *
# from flask_session import Session 
import json
from helper import execute_shell_command
import psutil
import json
import threading
import time
from collections import deque
from datetime import datetime
import pytz

app = Flask(__name__)
# app.config['SECRET_KEY'] = '343c855017e725321cb7f35b89c98b9e'
# app.config['SESSION_TYPE'] = 'filesystem'
# Session(app)


# File to store CPU usage data
# Global deque for storing up to 300 CPU usage records
cpu_data_queue = deque(maxlen=300)
lock = threading.Lock()  # Ensures thread-safe operations

def collect_cpu_usage():
    """Collect average CPU and memory usage over the last CPU_MEMORY_STATS_INTERVAL seconds."""
    cpu_usage_samples = []
    memory_usage_samples = []

    while True:
        start_time = time.time()
        while time.time() - start_time < CPU_MEMORY_STATS_INTERVAL:
            cpu_usage_samples.append(round(psutil.cpu_percent(interval=1),2))
            memory_usage_samples.append(round(psutil.virtual_memory().used / (1024 ** 3),2))

        # Calculate the average usage for the interval
        avg_cpu_usage = sum(cpu_usage_samples) / len(cpu_usage_samples) if cpu_usage_samples else 0
        avg_memory_usage = sum(memory_usage_samples) / len(memory_usage_samples) if memory_usage_samples else 0

        # Get current time
        ist = pytz.timezone("Asia/Kolkata")
        current_time = datetime.now(ist).strftime('%H:%M')

        with lock:
            cpu_data_queue.append({"time": current_time, "cpu": avg_cpu_usage, "memory": avg_memory_usage})

        # Clear samples for the next interval
        cpu_usage_samples.clear()
        memory_usage_samples.clear()


# Start the background thread for CPU monitoring
cpu_monitor_thread = threading.Thread(target=collect_cpu_usage, daemon=True)
cpu_monitor_thread.start()


@app.route('/execute_shell_com', methods=['GET'])
def execute_shell_com():
    try:
        command = request.args.get('shell_command', '')

        result = execute_shell_command(command)
        # print(result)
        # print("Status:", result["status"])
        # print("Output:", result["output"])
        if result["error"] and len(result["error"])!=0:
            print("Error:", result["error"])
            return jsonify({"status": result["status"],"message": f"Error occured. Executed {command} command on {hostname}.<br> Error : {result['error']}","output":result["output"]}), 200  # Internal Server Error
        else:
            return jsonify({"status": result["status"],"message": f"Executed {command} command on {hostname}.<br> {result['error']}","output":result["output"]}), 200  # Internal Server Error

    except Exception as e:
        return jsonify({"status": "error","message": f"An unexpected error occurred: {e}",}), 500  # Internal Server Error

@app.route('/get_input_files', methods=['GET'])
def get_input_files():
    with open(OSQUERY_TABLES_TEMPLATE_FILE) as tf:
        osq_template_data = json.load(tf)
    all_tables = list(osq_template_data.keys())
    
    # Concatenate the two lists
    input_files = os.listdir(INPUT_FILES_PATH) + all_tables
    input_files.sort()
    return jsonify({
            "status": "success",
            "message": f"Successfully fetched the inputfiles list from {hostname}",
            "input_files": input_files
        }), 200  # OK

@app.route('/get_inputfile_metadata', methods=['GET'])
def get_inputfile_metadata():
    inputfile_name = request.args.get('inputfile_name')

    inputfile_path = os.path.join(INPUT_FILES_PATH,inputfile_name)

    if os.path.isfile(inputfile_path):
        file_name_without_suffix = os.path.splitext(os.path.basename(inputfile_path))[0]
        metadata_filepath = os.path.join(INPUTFILES_METADATA_PATH, file_name_without_suffix+".json")
        with open(metadata_filepath) as m_f:
            metadata = json.load(m_f)
            return jsonify({
                "status": "success",
                "message": f"Successfully fetched the inputfile metadata for {inputfile_name} from {hostname}",
                "input_file_details": metadata,
                "modal_heading" : f"Metadata for '{inputfile_name}'"
            }), 200  # OK

    else:
        with open(OSQUERY_TABLES_TEMPLATE_FILE) as tf:
            osq_template_data = json.load(tf)
        
        if inputfile_name in osq_template_data:
            template = osq_template_data[inputfile_name]
            sample_record = {}
            note = "You have selected a direct table. Only records of this table will be used to form the msg on the go.<br>"
            try:
                sample_record = template["added"]["variation1"]
                note += f"Looks like this is an events table. It is recommended to use a pre-generated inputfile for this table if you wanted to calculate accuracies for events too.<br>However if you are only interested in {inputfile_name} table accuracies, you can proceed."
            except:
                sample_record = template["added"]
                
            return jsonify({
                    "status": "success",
                    "message": f"Successfully fetched the sample record for table {inputfile_name} from {hostname}",
                    "input_file_details": {f"Template for {inputfile_name} table in template file":template,
                                            "Number of tables per message":NUMBER_OF_TABLES_PER_MSG,
                                            "Number of records per table":NUMBER_OF_RECORDS_PER_TABLE,
                                            "Note":note,
                                            "Sample Record used in the msg formation":sample_record,
                                            "Tables Template file":OSQUERY_TABLES_TEMPLATE_FILE,
                                        },
                    "modal_heading" : f"Details for '{inputfile_name}' table as inputfile"

                }), 200  # OK
        
    return jsonify({
            "status": "error",
            "message": f"No details found for {inputfile_name} from {hostname}",
            "input_file_details": f"No details found for {inputfile_name}",
            "modal_heading" : f"Invalid"
        }), 404  # OK
        
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
                        domain_and_count[instance["domain"]] += '+' + str(instance["clients"])
                    else:
                        domain_and_count[instance["domain"]] = str(instance["clients"])
                for domain,expression in domain_and_count.items():
                    if '+' in expression:
                        domain_and_count[domain] = f'{eval(expression)} ( = {domain_and_count[domain]})'
            except Exception as e:
                print(f"Error while processing {testinput_file} contents")
        # Execute each bash command and collect the output
        for sim_type, command in bash_commands.items():
            command_result = execute_shell_command(command)
            # print(command)
            # print(command_result)
            command_outputs[sim_type] = command_result["output"]
            if command_result["error"] and len(command_result["error"])!=0:
                command_outputs[sim_type] += command_result["error"]
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

        with lock:
            current_cpu_usage_list = list(cpu_data_queue)
        
        return jsonify({
            "status": "success",
            "message": f"Successfully fetched {hostname} health information.",
            "table_data_result":{
                "process_instances": command_outputs,
                "domain_count":domain_and_count,
                "parameter_value":testinput_file_contents
            },
            "main_params":main_params,
            "load_remaining_dur_in_sec":remaining_load_duration,
            "cpu_stats":current_cpu_usage_list
        }), 200  # OK

    except Exception as e:
        return jsonify({"status": "error","message": f"An unexpected error occurred while checking health of {hostname}: {e}",}), 500  # Internal Server Error


@app.route('/update_load_params', methods=['POST'])
def update_load_params():
    try:
        updated_params = request.get_json()
        # print(updated_params)

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
