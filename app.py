from flask import Flask, request, jsonify
import os
from simulator_config_vars import SIMULATOR_SERVER_PORT,STACK_JSONS_PATH,hostname,testinput_file
from test_input_params import test_input_params
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
            "result_data": return_sims
        }), 200  # OK

    except json.JSONDecodeError as e:
        return jsonify({"status": "error","message": f"Failed to parse JSON from '{stack_json_file_path}': {e}"}), 400  # Bad Request

    except Exception as e:
        return jsonify({"status": "error","message": f"An unexpected error occurred: {e}"}), 500  # Internal Server Error

@app.route('/check_sim_health', methods=['GET'])
def check_sim_health():
    import subprocess

    bash_commands = {
        "endpointsim": "ps -ef | grep endpointsim -c",
        "node": "ps -ef | grep node -c",
    }
    command_outputs = {}

    try:
        testinput_result = {}
        if os.path.exists(testinput_file):
            try:
                with open(testinput_file, 'r') as json_file:
                    testinput_file_contents = json.load(json_file)
                instances = testinput_file_contents["instances"]
                for instance in instances:
                    testinput_result[instance["domain"]] = instance["clients"]
            except Exception as e:
                print(f"Error while processing {testinput_file} contents")
        # Execute each bash command and collect the output
        for sim_type, command in bash_commands.items():
            try:
                result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    command_outputs[sim_type] = result.stdout.strip()
                else:
                    command_outputs[sim_type] = f"Error: {result.stderr.strip()}"
            except Exception as e:
                command_outputs[sim_type] = f"Error executing command '{command}': {e}"

        # If no output could be retrieved for any simulator
        if not command_outputs:
            return jsonify({"status": "error","message": "Failed to retrieve simulator health information.",}), 500  # Internal Server Error

        # Success response with command outputs
        return jsonify({
            "status": "success",
            "message": f"Successfully fetched {hostname} health information.",
            "command_outputs": command_outputs,
            "test_input_params":test_input_params,
            "testinput_content":testinput_result
        }), 200  # OK

    except Exception as e:
        return jsonify({"status": "error","message": f"An unexpected error occurred: {e}",}), 500  # Internal Server Error


@app.route('/update_load_params', methods=['POST'])
def update_load_params():
    try:
        # Get the incoming form data
        updated_params = request.form.to_dict()

        if not updated_params:
            return jsonify({"status": "error","message": "No parameters provided in the request."}), 400  # Bad Request

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

        # Update the global dictionary
        test_input_params.update(updated_params)

        # Save the updated dictionary back to the Python file
        try:
            with open("test_input_params.py", 'w') as f:
                f.write("test_input_params = " + json.dumps(test_input_params, indent=4))
        except (IOError, OSError) as file_error:
            return jsonify({"status": "error","message": f"Failed to write to file: {str(file_error)}"}), 500  # Internal Server Error

        # Call the function with updated parameters
        try:
            create_testinput_files(test_input_params["stack_json_file"])
        except KeyError as key_error:
            return jsonify({"status": "error","message": f"Missing required key: {str(key_error)}"}), 400  # Bad Request
        except Exception as e:
            return jsonify({"status": "error","message": f"Failed to create new test input files: {str(e)}"}), 500  # Internal Server Error

        return jsonify({"status": "success","message": f"Parameters for {hostname} updated successfully. Please click on refresh button to view latest simulator parameters"}), 200  # OK

    except Exception as e:
        return jsonify({"status": "error","message": f"An unexpected error occurred: {str(e)}"}), 500  # Internal Server Error




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=SIMULATOR_SERVER_PORT,debug=True)
