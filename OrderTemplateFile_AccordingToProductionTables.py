# import random, os
import json
from simulator_config_vars import OSQUERY_TABLES_TEMPLATE_FILE

import csv

filename = '/Users/masabathulararao/Documents/osquery_simulator/generate_infile/top tables ingested in TB - last 15 days.csv'
# filename = '/Users/masabathulararao/Documents/osquery_simulator/generate_infile/top 20 events ingestion in Number - last 15 days.csv'


with open(filename, mode='r') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  # Skip the header
    prodiction_tables_order = [
        row[0] for row in csv_reader
        if row and row[1].strip() and float(row[1]) != 0
    ]

print("First Column Data (without header):")
print(prodiction_tables_order)

with open(OSQUERY_TABLES_TEMPLATE_FILE) as tf:
    osq_template_data = json.load(tf)

ordered_dict = {}

tables_matching = 0
tables_notmatching = 0
for key in prodiction_tables_order:
    if key in osq_template_data:
        tables_matching+=1
        ordered_dict[key] = osq_template_data[key]
    else:
        tables_notmatching+=1
        print(f"key {key} not present in the template file. Please add this a record of this table in the file")

print(f"Total tables in production order file are : {len(prodiction_tables_order)}")
print(f"Tables matching production file are : {tables_matching}")
print(f"Tables not matching production file are : {tables_notmatching}")
print('----------')
print(f"Total tables present in template file : {len(osq_template_data)}")
print(f"Tables Matched with prod list : {tables_matching}")
print(f"Tables that are not even present in prod list  : {len(osq_template_data)-tables_matching}")

for template_key in osq_template_data:
    if template_key not in ordered_dict:
        ordered_dict[template_key] = osq_template_data[template_key]
print(len(ordered_dict))
# with open(OSQUERY_TABLES_TEMPLATE_FILE, "w") as f:
#     json.dump(ordered_dict, f, indent=4)
