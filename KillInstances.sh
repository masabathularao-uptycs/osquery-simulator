#!/bin/bash



script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"


# Kill InitiateLoad.py process
echo "Stopping InitiateLoad.py processes..."
pgrep -f $script_dir/InitiateLoad.py | while read -r pid; do
  kill "$pid" 2>/dev/null
  echo "Terminated process with PID: $pid"
done

# Kill all instances of endpointsim
echo "Stopping endpointsim processes..."
killall endpointsim 2>/dev/null


echo "All specified processes have been terminated."
