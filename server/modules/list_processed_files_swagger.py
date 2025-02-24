import os
import json


def main():
    directory_path = './data/'

    # List directories of all processed files
    directories = [entry for entry in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, entry))]
    directories_json = {'Result': []}
    for directory in directories:
        directories_json['Result'].append({'ID': directory})
    print(json.dumps(directories_json, indent=4))


if __name__ == "__main__":
    main()