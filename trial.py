import requests
import json

SERVER_URL = "http://134.199.207.21"
INPUT_FILES = ['Input_Request.json', 'input2.json', 'input3.json', 'input4.json']

for i, input_file in enumerate(INPUT_FILES, start=1):
    try:
        with open(input_file) as f:
            input_json = json.load(f)

        response = requests.post(SERVER_URL + ":5000/receive", json=input_json, timeout=10)
        response.raise_for_status()  # Raise an exception if response status is not 200

        response_json = response.json()
        print(f"\nResponse for {input_file}:")
        #print(response_json)

        output_file = f"Output_Response_{i}.json"
        with open(output_file, "w") as out_f:
            json.dump(response_json, out_f, indent=4)

        print(f"Saved to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed for {input_file}: {e}")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {input_file}: {e}")
    except Exception as e:
        print(f"Error processing {input_file}: {e}")
