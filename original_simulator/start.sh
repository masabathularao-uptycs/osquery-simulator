#!/bin/bash

# List of sim machine hostnames or IP addresses
sims=("s1sim1a" "s1sim2a" "s1sim3a" "s1sim1b" "s1sim2b" "s1sim3b" "s1sim1c" "s1sim2c" "s1sim1d" "s1sim2d" "s1sim3c" "s1sim3d" )
#sims=("s1sim1a" "s1sim2a")
# Desired process count
desired_count=10

for sim in "${sims[@]}"; do
    echo "Connecting to $sim"
    ssh abacus@"$sim" 'cd /home/abacus/go_http/ && ./BringUpInstancesNewformat.sh'

    sleep 10  # Adjust the sleep time based on your needs

    while true; do
        current_count=$(ssh abacus@"$sim" "ps -ef | grep -c 'endpointsim'")
        if [ "$current_count" -ge "$desired_count" ]; then
            echo "Desired process count reached on $sim: $desired_count"
            break  # Exit the loop when desired count is reached
        else
            echo "Current process count on $sim: $current_count, waiting..."
            sleep 60  # Adjust the sleep time based on how frequently you want to check
        fi
    done
done
