import json
import requests

url = "https://chat-ai.academiccloud.de/v1/chat/completions"
api_key = 'API_KEY'
model = "meta-llama-3.1-8b-instruct"

headers = {
    "Accept": "application/json",
    "Authorization": 'Bearer '+api_key,
    "Content-Type": "application/json",
    "inference-service": "saia-openai-gateway",
}

data = {
    "model": model,
    "messages": [
        {"role": "system", "content": prompt},
        {"role": "user", "content": input},
    ],
    "enable-tools": True,
    "arcana": {
        "id": "jihoo.chung01/ace_nutshell"
    },
    "temperature": 0.0,
    "top_p": 0.05,
}


try:
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    result = response.json()
    print(result["choices"][0]["message"]["content"])

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP Error: {http_err}")
    print(f"{response.text}")
except Exception as err:
    print(f"Error: {err}")
