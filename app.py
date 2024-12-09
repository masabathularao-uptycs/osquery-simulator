from flask import Flask, render_template, request, jsonify, Response, send_from_directory, url_for, flash, session
import os
from simulator_config_vars import SIMULATOR_SERVER_PORT,STACK_JSONS_PATH
from test_input_params import test_input_params
import time
from queue import Queue
from flask_session import Session 
import json
from CreateTestinputFiles import create_testinput_files

app = Flask(__name__)
# app.config['SECRET_KEY'] = '343c855017e725321cb7f35b89c98b9e'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

OSQUERY_DATA_LOAD_NAMES = ["multicustomer","singlecustomer"]
OSQUERY_CONTROLPLANE_LOAD_NAMES = ["controlplane"]


@app.route('/get_osquery_simulator_names', methods=['GET'])
def get_osquery_simulator_names():
    # Get the 'name' parameter from the request
    stack_json_file_name = request.args.get('stack_json_file_name')
    loadname = request.args.get('loadname')

    if str(loadname).lower() not in OSQUERY_DATA_LOAD_NAMES+OSQUERY_CONTROLPLANE_LOAD_NAMES:
        return jsonify({"error": f"loadname should be in {OSQUERY_CONTROLPLANE_LOAD_NAMES} or {OSQUERY_DATA_LOAD_NAMES}"})

    # If no name is provided, return an error response
    if not stack_json_file_name:
        return jsonify({"error": "Missing 'stack_json_file_name' parameter"})
    
    stack_json_file_path = f"{STACK_JSONS_PATH}/{stack_json_file_name}.json"

    if not os.path.exists(stack_json_file_path):
        return jsonify({"error": f"{stack_json_file_path} file doesnt exist"})

    with open(stack_json_file_path,'r') as json_file:
        json_file = json.load(json_file)

    if loadname in OSQUERY_DATA_LOAD_NAMES:
        return_sims =  json_file["osquery_data_load_params"]["sims"]
    if loadname in OSQUERY_CONTROLPLANE_LOAD_NAMES:
        return_sims =  json_file["osquery_controlplane_load_params"]["sims"]
    
    return jsonify({"osquery_load_sims": return_sims})

@app.route('/check_sim_liveliness', methods=['GET'])
def check_sim_liveliness():
    return jsonify({"message": "healthy"})

@app.route('/update_load_params', methods=['POST'])
def update_load_params():
    # Get the incoming data
    updated_params = request.form.to_dict()

    # Dynamically cast based on the type in the existing dictionary
    for key, value in updated_params.items():
        if key in test_input_params:
            # Attempt to cast to the type of the existing value in test_input_params
            try:
                current_type = type(test_input_params[key])
                if current_type is int:
                    updated_params[key] = int(value)
                elif current_type is float:
                    updated_params[key] = float(value)
                elif current_type is bool:
                    updated_params[key] = value.lower() in ['true', '1', 'yes']
                else:
                    updated_params[key] = value  # Keep as string if not a recognized type
            except ValueError:
                # If casting fails, keep the value as-is (string)
                pass

    # Update the global dictionary
    test_input_params.update(updated_params)

    # Save updated dictionary back to the Python file
    with open("test_input_params.py", 'w') as f:
        f.write("test_input_params = " + json.dumps(test_input_params, indent=4))

    # Call the function with updated parameters
    create_testinput_files(test_input_params["stack_json_file"])
    
    return jsonify({"message": f"updated"})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=SIMULATOR_SERVER_PORT,debug=True)
