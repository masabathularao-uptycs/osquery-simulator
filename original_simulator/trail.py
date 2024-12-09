import json
from datetime import datetime

# Load JSON data from file
with open("trial.json") as tf:
    osq_template_data = json.load(tf)

# Filtered data
filtered_data = {}

# Iterate over data and filter
for i in osq_template_data['data']:
    if i["name"] == "process_events" and i['columns']['cmdline']=="cat /etc/passwd":
        filtered_data = i

osq_template_data['data'] = [filtered_data]
dest_file = "trail.log"

# Write data to the log file
with open(dest_file, "w") as out_fd:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out_fd.write(now)
    out_fd.write("\n")
    out_fd.write(json.dumps(osq_template_data))
    out_fd.write("\n")
