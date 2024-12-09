#!/bin/bash

for i in s1sim3a s1sim4a s1sim5a s1sim6a s1sim1b s1sim2b s1sim3b s1sim4b s1sim5b s1sim6b s1sim1c s1sim2c s1sim3c s1sim4c s1sim5c s1sim6c s1sim1d s1sim2d s1sim3d s1sim4d s1sim5d s1sim6d; do
  # Generate a unique output file name based on the server name
  output_file="ssh_output_$i.log"
  
  # Clear the output file (optional, remove if you want to append)
  > "$output_file"
  
  # Run the SSH command and redirect output to the unique file
  ssh abacus@$i "hostname; cd ~/go_http/ && /bin/bash BringUpInstances.sh;sleep 30;exit" >> "$output_file" 2>&1
done

