from flask import Blueprint, request, jsonify
import os

run_bp = Blueprint('run', __name__)

currentCommand = 'echo "Please check the instructions on the swagger interface"'

@run_bp.route('/setCommand', methods=['POST'])
def set_command():
    global currentCommand
    data = request.get_json()
    new_command = data.get('command')

    if not new_command:
        return jsonify({"error": "Command is required"}), 400
    
    currentCommand = new_command
    return jsonify({"message": "Command updated successfully to "+currentCommand}), 200


@run_bp.route('/', methods=['POST'])
def run_command():
  
    try:
        data = request.get_json()
        command = currentCommand
        for k, v in data.items():
            command = command.replace('{'+str(k)+'}', str(v))

        result = os.popen(command).read()
        return jsonify({"stdout": result}), 200 
    except Exception as err:
        return jsonify({"error": str(err)}), 400

