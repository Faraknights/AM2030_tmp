import os
import json
import sys


def main():

    input_id = sys.stdin.read()
    directory_path = './segments/'
    file_segment_directory = os.path.join(directory_path, input_id)
    if not os.path.isdir(file_segment_directory):
        print("The ID does not exist")
        return  # Exit the program with an error code

    segment_directory_dic = []
    for filename in os.listdir(file_segment_directory):
        file_path = os.path.join(file_segment_directory, filename)
        if os.path.isfile(file_path) and filename.endswith('.json'):
            with open(file_path, 'r') as file:
                data_dic = json.load(file)
                data_dic['filename'] = filename
                segment_directory_dic.append(data_dic)
    segment_directory_dic.sort(key=lambda x: x.get('turn', 0))
    result_segment = {'Result': segment_directory_dic}
    print(json.dumps(result_segment, indent=4))


if __name__ == "__main__":
    main()