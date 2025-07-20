import requests
import json

SERVER_URL = "http://134.199.207.21"

INPUT_JSON_FILE = "input2.json"
OUTPUT_JSON_FILE = "Output_Response2.json"

# Load input JSON
with open(INPUT_JSON_FILE) as f:
    input_json = json.load(f)

# Send POST request
response = requests.post(SERVER_URL + ":5000/receive", json=input_json, timeout=10)

# Get and print response JSON
response_json = response.json()
print(response_json)

# Save output to file
with open(OUTPUT_JSON_FILE, "w") as f:
    json.dump(response_json, f, indent=4)
