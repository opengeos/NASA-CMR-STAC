import json
import os
import pandas as pd
from pystac_client import Client

out_dir = "datasets"

url = "https://cmr.earthdata.nasa.gov/stac"

root = Client.open(url, headers=[])

catalogs = []

for link in root.get_child_links():
    if link.rel == "child":
        catalogs.append(link.target)

datasets = []

for catalog in catalogs:

    try:
        cat = Client.open(catalog, headers=[])
        print(cat.title)
        for collection in cat.get_all_collections():
            data = collection.to_dict()
            print(data["id"])
            dataset = {}
            output = out_dir + "/" + data["id"].replace("/", "_") + ".json"
            if not os.path.exists(os.path.dirname(output)):
                os.makedirs(os.path.dirname(output))
            with open(output, "w") as f:
                json.dump(data, f, indent=4)

            dataset["id"] = data["id"].strip()
            dataset["title"] = data["title"].strip()
            dataset["catalog"] = cat.title.strip()

            start_date = data["extent"]["temporal"]["interval"][0][0]
            end_date = data["extent"]["temporal"]["interval"][0][1]

            if start_date is not None:
                dataset["state_date"] = start_date.split("T")[0]
            else:
                dataset["state_date"] = ""

            if end_date is not None:
                dataset["end_date"] = end_date.split("T")[0]
            else:
                dataset["end_date"] = ""
            dataset["bbox"] = ", ".join(
                [str(coord) for coord in data["extent"]["spatial"]["bbox"][0]]
            )

            url = ""
            metadata = ""
            href = ""

            for l in data["links"]:
                if l["rel"] == "about":
                    metadata = l["href"]
                if l["rel"] == "self":
                    href = l["href"]
                if l["rel"] == "via":
                    url = l["href"]

            dataset["url"] = url
            dataset["metadata"] = metadata
            dataset["href"] = href

            dataset["description"] = (
                data["description"]
                .replace("\n", " ")
                .replace("\r", " ")
                .replace("\\u", " ")
                .replace("                 ", " ")
            )

            dataset["license"] = data["license"]

            datasets.append(dataset)
    except Exception as e:
        print("Error: ", catalog)
        print(e)

print("Total datasets: ", len(datasets))

df = pd.DataFrame(datasets)
df.sort_values(by=["id"], inplace=True)
df.drop(columns=["href", "metadata"]).to_csv(
    "nasa_cmr_catalog.tsv", index=False, sep="\t"
)

with open("nasa_cmr_catalog.json", "w") as f:
    json.dump(df.to_dict("records"), f, indent=4)
