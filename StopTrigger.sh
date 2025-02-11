#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"


# Kill InitiateLoad.py process
echo "Stopping LoadTrigger.py processes..."
pgrep -f $script_dir/LoadTrigger.py | while read -r pid; do
  kill "$pid" 2>/dev/null
  echo "Terminated process with PID: $pid"
done

echo "All specified processes have been terminated."
