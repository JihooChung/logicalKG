import requests

url = "https://chat-ai.academiccloud.de/v1/chat/completions"
api_key = '8333a36daa801574977831d75be754b1'
model = "gemma-4-31b-it"
#model = "medgemma-27b-it"


with open("logicalKG/drs_to_kg/oneshot_STRICT_prompt.txt", "r") as file:
    prompt = file.read()

SAMPLE_INDEX = 1

with open("logicalKG/sample/samples_STRICT_drs.txt", "r") as file:
    samples = {}
    current = None
    for line in file:
        if line.startswith("#Sample"):
            current = int(line.split(":")[0].replace("#Sample", ""))
            samples[current] = []
        elif current is not None:
            samples[current].append(line)
    sample = "".join(samples[SAMPLE_INDEX]).strip()


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
        {"role": "user", "content": sample},
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
    print(result["choices"][0]["message"]["content"].split("References:")[0].strip())

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP Error: {http_err}")
    print(f"{response.text}")
except Exception as err:
    print(f"Error: {err}")