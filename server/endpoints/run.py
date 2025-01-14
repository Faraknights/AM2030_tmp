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
    return jsonify({"message": "Command updated successfully"}), 200


@run_bp.route('/', methods=['POST'])
def run_command():
    data = request.get_json()
    inputFile = data.get('inputFile')
    outputFile = data.get('outputFile') 

    if inputFile:
        if not os.path.exists(inputFile):
            return jsonify({"error": "Invalid input file"}), 400
        command = currentCommand.replace('{inputFile}', inputFile)
    else:
        command = currentCommand.replace('{inputFile}', 'default_value')

    if outputFile:
        command = command.replace('{outputFile}', outputFile)
        command += f" && echo 'The output file is: {outputFile}'"
    else:
        return jsonify({"error": "Output file is required"}), 400
    
    result = os.popen(command).read()
    
    return jsonify({"stdout": result}), 200
