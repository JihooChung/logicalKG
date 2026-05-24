import requests

url = "https://attempto.ifi.uzh.ch/service/ape"

sample = "A human is a man and John is the human."

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
