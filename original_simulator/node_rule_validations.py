import json
import ast

input_lines = 3600
dns_lookup_events = {'dns_lookup_events_alert-builder-added':0, 'dns_lookup_events_1_alert-builder-added':0, 'dns_lookup_events_2_alert-builder-added':0, 'dns_lookup_events_3_alert-builder-added':0, 'dns_lookup_events_4_alert-builder-added':0}
process_events = {'process_events_alert-builder-added':0, 'process_events_1_alert-builder-added':0, 'process_events_2_alert-builder-added':0, 'process_events_3_alert-builder-added':0, 'process_events_4_alert-builder-added':0, 'process_events_5_alert-builder-added':0, 'process_events_6_alert-builder-added':0, 'process_events_7_alert-builder-added':0, 'process_events_8_alert-builder-added':0, 'process_events_9_alert-builder-added':0, 'process_events_10_alert-builder-added':0}
socket_events = {'socket_events_alert-builder-added':0, 'socket_events_1_alert-builder-added':0, 'socket_events_2_alert-builder-added':0, 'socket_events_3_alert-builder-added':0, 'socket_events_4_alert-builder-added':0, 'socket_events_5_alert-builder-added':0, 'socket_events_6_alert-builder-added':0}
process_file_events = {'process_file_events_alert-builder-added':0, 'process_file_events_3_alert-builder-added':0, 'process_file_events_4_alert-builder-added':0, 'process_file_events_5_alert-builder-added':0, 'process_file_events_6_alert-builder-added':0, 'process_file_events_7_alert-builder-added':0, 'process_file_events_8_alert-builder-added':0, 'process_file_events_9_alert-builder-added':0, 'process_file_events_10_alert-builder-added':0}
req_tables = ['process_events', 'process_file_events', 'socket_events', 'dns_lookup_events']
with open("rhel7-6tab_12rec.log", "r") as fin:
    line_no = 1
    for line in fin:
        if line_no % 2 == 0 and line_no <= input_lines: 
            lines = json.loads(line)
            #print(line)
            #print(len(lines["data"]))
            for table_details in lines["data"]:
                #print(table_details)
                if table_details['name'] == 'process_events':
                    index1 = table_details['columns']['auid']
                    index2 = table_details['columns']['uid']
                    #rows = table_details['rows']
                    if index1 == '0' or index2 == '0':
                        process_events['process_events_alert-builder-added'] += 1
                    if '/bin/sh' in table_details['columns']['path']:
                        if '/bin/mysql' in table_details['columns']['ancestor_list']:
                            process_events['process_events_5_alert-builder-added'] += 1
                        if '/bin/php' in table_details['columns']['ancestor_list']:
                            process_events['process_events_1_alert-builder-added'] += 1
                        if '/bin/awk' in table_details['columns']['ancestor_list']:
                            process_events['process_events_10_alert-builder-added'] += 1
                    if '/proc/' in table_details['columns']['cmdline']:
                        process_events['process_events_2_alert-builder-added'] += 1
                    if 'base64' in table_details['columns']['cmdline']:
                        process_events['process_events_3_alert-builder-added'] += 1
                    if ('bin/osascript' in table_details['columns']['path']) or ('shell' in table_details['columns']['cmdline']):
                        process_events['process_events_4_alert-builder-added'] += 1
                    if table_details['columns']['exe_name'] == 'wmic.exe':
                        process_events['process_events_7_alert-builder-added'] += 1
                    if table_details['columns']['version_info'] == "Net Command":
                        process_events['process_events_8_alert-builder-added'] += 1
                    if 'rmmod' in table_details['columns']['cmdline']:
                        process_events['process_events_9_alert-builder-added'] += 1
                if table_details['name'] == 'socket_events':
                    if (table_details['columns']['action'] == 'connect') and (table_details['columns']['family'] == '2') and (table_details['columns']['type'] == '2') and (table_details['columns']['exe_name'] == 'node'):
                        socket_events['socket_events_alert-builder-added'] += 1
                        socket_events['socket_events_1_alert-builder-added'] += 1
                        socket_events['socket_events_2_alert-builder-added'] += 1
                    if (table_details['columns']['action'] == 'connect') and (table_details['columns']['family'] == '2') and (table_details['columns']['type'] == '2') and (table_details['columns']['remote_address'] == '169.254.169.254') and (table_details['columns']['is_container_process'] == '1'):
                        socket_events['socket_events_3_alert-builder-added'] += 1
                    if (table_details['columns']['action'] == 'connect') and (table_details['columns']['cmdline'] == '-e') and (table_details['columns']['path'] == '/usr/bin/ruby'):
                        socket_events['socket_events_4_alert-builder-added'] += 1
                    if "9.5.4.3" in table_details['columns']['remote_address'] or "169.254.169.254" in table_details['columns']['remote_address']:
                        socket_events['socket_events_5_alert-builder-added'] += 1
                    if "malware" in table_details['columns']['remote_address']:
                        socket_events['socket_events_6_alert-builder-added'] += 1

                if table_details['name'] == 'dns_lookup_events':
                    index = table_details['columns']['question']
                    #rows = table_details['rows']
                    #for row in rows:
                    if 'malware' in index:
                        dns_lookup_events['dns_lookup_events_1_alert-builder-added'] += 1
                        dns_lookup_events['dns_lookup_events_2_alert-builder-added'] += 1
                    if 'dga' in index:
                        dns_lookup_events['dns_lookup_events_3_alert-builder-added'] += 1
                    if 'phishing' in index:
                        dns_lookup_events['dns_lookup_events_4_alert-builder-added'] += 1
                    if 'coinminer' in index:
                        dns_lookup_events['dns_lookup_events_alert-builder-added'] += 1

                if table_details['name'] == 'process_file_events':
                    #rows = table_details['rows']
                    #for row in rows:
                    if (table_details['columns']['path'] == '/etc/passwd') and (table_details['columns']['operation'] == 'open') and (table_details['columns']['flags'] == 'O_WRONLY'):
                        process_file_events['process_file_events_3_alert-builder-added'] += 1
                        process_file_events['process_file_events_4_alert-builder-added'] += 1
                    if (table_details['columns']['operation'] == 'chmod') and (table_details['columns']['flags'] == 'S_ISUID'):
                        process_file_events['process_file_events_alert-builder-added'] += 1
                    if (table_details['columns']['operation'] == 'rename') and (table_details['columns']['dest_path'] == '/.'):
                        process_file_events['process_file_events_5_alert-builder-added'] += 1
                    if table_details['columns']['operation'] == 'chown32':
                        process_file_events['process_file_events_6_alert-builder-added'] += 1
                    if (table_details['columns']['operation'] == 'write') and (table_details['columns']['executable'] == 'System') and (('.exe' in table_details['columns']['path']) or ('4D5A9000' in table_details['columns']['magic_number'])):
                        process_file_events['process_file_events_7_alert-builder-added'] += 1
                    if (table_details['columns']['operation'] == 'rename'):
                        process_file_events['process_file_events_8_alert-builder-added'] += 1
                    if ('/etc/ld.so.conf' in table_details['columns']['path']) and (table_details['columns']['operation'] == 'open') and (table_details['columns']['flags'] == 'O_WRONLY'):
                        process_file_events['process_file_events_9_alert-builder-added'] += 1
                    if (table_details['columns']['path'] == '/etc/passwd') and (table_details['columns']['operation'] == 'open') and (table_details['columns']['is_container_process'] == '0'):
                        process_file_events['process_file_events_10_alert-builder-added'] += 1

        else:
            pass 
        line_no += 1  
    print(dns_lookup_events) 
    print(process_events)
    print(socket_events)
    print(process_file_events)
    dict1 = {}
    dict1.update(dns_lookup_events)
    dict1.update(process_events)
    dict1.update(socket_events)
    dict1.update(process_file_events)
    print(dict1)
    print((sum(dict1.values()))*25)
