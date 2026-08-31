import pandas as pd
import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input_path", type=str, default="./data/ace/ace_list.csv")
parser.add_argument("--output_path", type=str, default="./data/drs/drs_list.csv")
args = parser.parse_args()

df = pd.read_csv(args.input_path)
url = "https://attempto.ifi.uzh.ch/service/ape"

drs_rows = []

for index, row in df.iterrows():
    abstract_id = row["abstract_id"]
    drs_parts = []

    for line in row["ace"].splitlines():
        if not line.strip():
            continue

        params = {
            "text": line,
            "solo": "drspp",
        }

        try:
            response = requests.get(url, params=params)

            if response.status_code == 200:
                lines = [ln.strip() for ln in response.text.splitlines() if ln.strip()]
                if not lines:
                    continue
                if len(lines) == 1:
                    drs_text = lines[0]
                else:
                    drs_text = lines[0] + " " + ",".join(lines[1:])
                drs_parts.append(drs_text)
            else:
                print(f"Error: {response.status_code}")
                print("Message:", response.text)

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
    print(drs_parts)
    drs_rows.append({
        "abstract_id": abstract_id,
        "drs": "\n".join(drs_parts),
    })

drs_df = pd.DataFrame(drs_rows)
drs_df.to_csv(args.output_path, index=False)
