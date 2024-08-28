from helper import run_commands
import math

testinput_path = "testinput.json"

sims_list = ["s1sim1a","s1sim1b","s1sim1c", "s1sim1d", "s1sim2a", "s1sim2b", "s1sim2c", "s1sim2d", "s1sim3a", "s1sim3b","s1sim3c", "s1sim3d"]
instances_per_each_sim = 32
control_testinput_base_path = "/home/abacus/simulator"

total_number_of_assets = 30_000

update_params = {
"clients" : math.ceil(total_number_of_assets/(instances_per_each_sim*len(sims_list))),
}

main_node = sims_list[0]

print(update_params)
run_commands(control_testinput_base_path,sims_list,update_params,testinput_path,main_node,None)





