import requests

url = "https://attempto.ifi.uzh.ch/service/ape"

SAMPLE_INDEX = 1 

with open("logicalKG/sample/samples_STRICT_ace.txt", "r") as file:
    samples = {}
    current = None
    for line in file:
        if line.strip() == "":
            continue
        if line.startswith("#Sample"):
            current = int(line.split(":")[0].replace("#Sample", ""))
            samples[current] = []
        elif current is not None:
            samples[current].append(line)

for sample in samples[SAMPLE_INDEX]:

    params = {
        "text": sample,
        "solo": "drspp"                  
    }

    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            print(response.text)
        else:
            print(f"Error: {response.status_code}")
            print("Message:", response.text)

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
