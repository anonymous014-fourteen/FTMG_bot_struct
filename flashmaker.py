import pandas as pd
import time
import requests
import os

WEBHOOK = os.environ["WEBHOOK"]
total_start = time.time()

DEFAULT_DESC = "this is a placeholder description which will be replaced with an actual one, sit tight and wait for the development to be finished"

class Item:
    def __init__(self, name):
        self.name = name
        self.avg_price = 0
        self.abs_min = 0
        self.very_low = 0
        self.low = 0
        self.high = 0
        self.very_high = 0
        self.abs_max = 0
        self.description = ""
        self.category = None

items = {}

CATEGORY_SHEETS = [
    "Bags",
    "Materials",
    "Trash Caches",
    "Common Caches",
    "High Quality Caches",
    "Rare Caches",
    "Legendary Caches",
    "Epic Caches",
    "Heals"
]

url = "https://docs.google.com/spreadsheets/d/1rJVbEIDKQUth7xVLxu5s0O_RAInNIfx9ri-HvSzaVow/export?format=xlsx"

fields = ["avg_price", "abs_min", "very_low", "low", "high", "very_high", "abs_max"]

print("Read begin")
read_start = time.time()

xls = pd.ExcelFile(url)

for sheet_name in CATEGORY_SHEETS:
    df = pd.read_excel(xls, sheet_name=sheet_name, header=1)
    df.columns = ["name"] + fields + ["description"]

    sheet_data = df.set_index("name").to_dict(orient="index")

    for name, values in sheet_data.items():
        key = f"{sheet_name}::{name}"
        item = Item(name)

        for f in fields:
            val = values[f]
            if pd.isna(val):
                val = 0
            else:
                val = float(val)
            setattr(item, f, val)

        desc = values["description"]
        if pd.isna(desc) or str(desc).strip() == "":
            desc = DEFAULT_DESC

        item.description = desc
        item.category = sheet_name

        items[key] = item

read_end = time.time()
print(f"Read time: {read_end - read_start:.2f} seconds")

print("Build content")
build_start = time.time()

lines = []
lines.append("items = {\n")

cur_category = "empty"

for key, item in items.items():
    item = items[key]

    lines.append(f'    "{key}": {{\n')
    lines.append(f'        "name": {repr(item.name)},\n')
    lines.append(f'        "avg_price": {item.avg_price},\n')
    lines.append(f'        "abs_min": {item.abs_min},\n')
    lines.append(f'        "very_low": {item.very_low},\n')
    lines.append(f'        "low": {item.low},\n')
    lines.append(f'        "high": {item.high},\n')
    lines.append(f'        "very_high": {item.very_high},\n')
    lines.append(f'        "abs_max": {item.abs_max},\n')
    lines.append(f'        "description": {repr(item.description)},\n')
    lines.append(f'        "category": {repr(item.category)}\n')
    lines.append("    },\n")

    if item.category != cur_category:
        if cur_category != "empty":
            print("finished", cur_category)
        cur_category = item.category
        print("started ", item.category)

lines.append("}\n")

new_content = "".join(lines)

build_end = time.time()
print(f"Build time: {build_end - build_start:.2f} seconds")

print("Compare + send")
compare_start = time.time()

old_content = ""
FILE = "memory_flash.py"

if os.path.exists(FILE):
    with open(FILE, "r", encoding="utf-8") as f:
        old_content = f.read()

if new_content == old_content:
    print("no change detected")

    requests.post(WEBHOOK, json={
        "content": "nothing seems to have changed"
    })
else:
    print("change detected, writing + sending")

    with open(FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    with open(FILE, "rb") as f:
        requests.post(
            WEBHOOK,
            data={"content": "flash updated"},
            files={"file": f}
        )

compare_end = time.time()
print(f"Compare time: {compare_end - compare_start:.2f} seconds")

total_end = time.time()
print(f"Total time: {total_end - total_start:.2f} seconds")
