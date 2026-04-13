import pandas as pd
import time
import requests
import os

WEBHOOK = os.environ["WEBHOOK"]
total_start = time.time()

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

    def __repr__(self):
        return f"{self.name} ({self.category})"


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

print("Read  begin")
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
            setattr(item, f, values[f])

        item.description = values["description"]
        item.category = sheet_name

        items[key] = item

read_end = time.time()
print(f"Read time: {read_end - read_start:.2f} seconds")

print("write begin")
write_start = time.time()
cur_category = "empty"
with open("memory_flash.py", "w", encoding="utf-8") as f:
    f.write("items = {\n")

    for key, item in items.items():
        f.write(f'    "{key}": {{\n')
        f.write(f'        "name": {repr(item.name)},\n')
        f.write(f'        "avg_price": {item.avg_price},\n')
        f.write(f'        "abs_min": {item.abs_min},\n')
        f.write(f'        "very_low": {item.very_low},\n')
        f.write(f'        "low": {item.low},\n')
        f.write(f'        "high": {item.high},\n')
        f.write(f'        "very_high": {item.very_high},\n')
        f.write(f'        "abs_max": {item.abs_max},\n')
        f.write(f'        "description": {repr(item.description)},\n')
        f.write(f'        "category": {repr(item.category)}\n')
        f.write("    },\n")
        if item.category != cur_category:
            if cur_category != "empty":
                print("finished", cur_category)
            cur_category = item.category
            print("started ", item.category)
    f.write("}\n")
with open("memory_flash.py", "rb") as f:
    requests.post(WEBHOOK, files={"file": f})
write_end = time.time()
print(f"Write time: {write_end - write_start:.2f} seconds")

    
