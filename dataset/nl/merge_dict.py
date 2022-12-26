import json
import sys

def merge_json_dicts(*dicts, path):
    merged_dict = {}
    for dictionary in dicts:
        merged_dict.update(dictionary)

    # Write the merged dictionary to a new file
    with open(path+"/vocabulary.json", "w") as f:
        json.dump(merged_dict, f)

# Load the dictionaries from the files
dict1_file = sys.argv[1]
dict2_file = sys.argv[2]
path = sys.argv[3]

with open(dict1_file, "r") as f:
    dict1 = json.load(f)

with open(dict2_file, "r") as f:
    dict2 = json.load(f)

# Merge the dictionaries
merge_json_dicts(dict1, dict2, path=path)