from helper import run_commands
import math

testinput_path = "testinput.json"

sims_list = ["s1sim1a","s1sim1b","s1sim1c", "s1sim1d", "s1sim2a", "s1sim2b", "s1sim2c", "s1sim2d", "s1sim3a", "s1sim3b","s1sim3c", "s1sim3d"]
instances_per_each_sim = 32
multi_testinput_base_path = "/home/abacus/go_http"
original_multi_testinput_path = "sing_cust_testinput.json"

total_number_of_assets = 10_000
duration_of_load_in_hrs = 10

update_params = {
"clients" : math.ceil(total_number_of_assets/(instances_per_each_sim*len(sims_list))),
"endline" : 1800 * duration_of_load_in_hrs,
"inputfile" : "rhel7-6tab_12rec.log"
}

main_node = sims_list[0]

print(update_params )
run_commands(multi_testinput_base_path,sims_list,update_params,testinput_path,main_node,original_multi_testinput_path)
