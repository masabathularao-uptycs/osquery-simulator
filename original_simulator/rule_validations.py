import json
import ast

input_lines = 300
dns_lookup_events = {'dns_lookup_events_alert-builder-added':0, 'dns_lookup_events_1_alert-builder-added':0, 'dns_lookup_events_2_alert-builder-added':0, 'dns_lookup_events_3_alert-builder-added':0, 'dns_lookup_events_4_alert-builder-added':0}
process_events = {'process_events_alert-builder-added':0, 'process_events_1_alert-builder-added':0, 'process_events_2_alert-builder-added':0, 'process_events_3_alert-builder-added':0, 'process_events_4_alert-builder-added':0, 'process_events_5_alert-builder-added':0, 'process_events_6_alert-builder-added':0, 'process_events_7_alert-builder-added':0, 'process_events_8_alert-builder-added':0, 'process_events_9_alert-builder-added':0, 'process_events_10_alert-builder-added':0}
socket_events = {'socket_events_alert-builder-added':0, 'socket_events_1_alert-builder-added':0, 'socket_events_2_alert-builder-added':0, 'socket_events_3_alert-builder-added':0, 'socket_events_4_alert-builder-added':0, 'socket_events_5_alert-builder-added':0, 'socket_events_6_alert-builder-added':0}
process_file_events = {'process_file_events_alert-builder-added':0, 'process_file_events_3_alert-builder-added':0, 'process_file_events_4_alert-builder-added':0, 'process_file_events_5_alert-builder-added':0, 'process_file_events_6_alert-builder-added':0, 'process_file_events_7_alert-builder-added':0, 'process_file_events_8_alert-builder-added':0, 'process_file_events_9_alert-builder-added':0, 'process_file_events_10_alert-builder-added':0}
req_tables = ['process_events', 'process_file_events', 'socket_events', 'dns_lookup_events']
with open("osq_custom_72_records_40k.out", "r") as fin:
    line_no = 1
    for line in fin:
        if line_no % 2 == 0 and line_no <= input_lines: 
            line = json.loads(line)
            print(line)
            for table_details in line:
                print(table_details)
                if table_details['name'] == 'dns_lookup_events':
                    index = table_details['columns'].index('question')
                    rows = table_details['rows']
                    for row in rows:
                        if 'malware' in row[index]:
                            dns_lookup_events['dns_lookup_events_1_alert-builder-added'] += 1
                            dns_lookup_events['dns_lookup_events_2_alert-builder-added'] += 1
                        if 'dga' in row[index]:
                            dns_lookup_events['dns_lookup_events_3_alert-builder-added'] += 1
                        if 'phishing' in row[index]:
                            dns_lookup_events['dns_lookup_events_4_alert-builder-added'] += 1
                        if 'coinminer' in row[index]:
                            dns_lookup_events['dns_lookup_events_alert-builder-added'] += 1
                if table_details['name'] == 'process_events':
                    index1 = table_details['columns'].index('auid')
                    index2 = table_details['columns'].index('uid')
                    rows = table_details['rows']
                    for row in rows:
                        if row[index1] == '0' or row[index2] == '0':
                            process_events['process_events_alert-builder-added'] += 1
                        if '/bin/sh' in row[table_details['columns'].index('path')]:
                            if '/bin/php' in row[table_details['columns'].index('ancestor_list')]:
                                process_events['process_events_1_alert-builder-added'] += 1
                            if '/bin/mysql' in row[table_details['columns'].index('ancestor_list')]:
                                process_events['process_events_5_alert-builder-added'] += 1
                            if '/bin/awk' in row[table_details['columns'].index('ancestor_list')]:
                                process_events['process_events_10_alert-builder-added'] += 1
                        if '/proc/' in row[table_details['columns'].index('cmdline')]:
                            process_events['process_events_2_alert-builder-added'] += 1
                        if 'base64' in row[table_details['columns'].index('cmdline')]:
                            process_events['process_events_3_alert-builder-added'] += 1
                        if ('bin/osascript' in row[table_details['columns'].index('path')]) and (('shell' in row[table_details['columns'].index('cmdline')]) or ('python' in row[table_details['columns'].index('cmdline')])):
                            #print(row[table_details['columns'].index('path')])
                            #print(row[table_details['columns'].index('cmdline')])
                            process_events['process_events_4_alert-builder-added'] += 1
                        # if (row[table_details['columns'].index('exe_name')] == 'docker'):
                        #     rows = table_details['rows']
                        #     for row in rows:
                        #         #print(row)
                        #         inx = table_details['columns'].index('ancestor_list')
                        #         #print(inx)
                        #         ele = row[inx]
                        #         #print(ele)
                        #         ele = json.loads(ele)
                        #         for el in ele:
                        #             #print(el)
                        #             if el['path']=='/bin/at':    
                        #                 process_events['process_events_6_alert-builder-added'] += 1
                        if row[table_details['columns'].index('exe_name')] == 'wmic.exe':
                            process_events['process_events_7_alert-builder-added'] += 1
                        if row[table_details['columns'].index('version_info')] == "Net Command":
                            process_events['process_events_8_alert-builder-added'] += 1
                        if 'rmmod' in row[table_details['columns'].index('cmdline')]:
                            process_events['process_events_9_alert-builder-added'] += 1
                if table_details['name'] == 'socket_events':
                    rows = table_details['rows']
                    for row in rows:
                        if (row[table_details['columns'].index('action')] == 'connect') and (row[table_details['columns'].index('family')] == '2') and (row[table_details['columns'].index('type')] == '2'):
                            #socket_events['socket_events_1_alert-builder-added'] += 1
                            socket_events['socket_events_alert-builder-added'] += 1
                        if (row[table_details['columns'].index('action')] == 'connect') and (row[table_details['columns'].index('family')] == '2') and (row[table_details['columns'].index('type')] == '2') and (row[table_details['columns'].index('exe_name')] == 'node'):
                            #socket_events['socket_events_alert-builder-added'] += 1
                            #socket_events['socket_events_1_alert-builder-added'] += 1
                            socket_events['socket_events_2_alert-builder-added'] += 1
                        if (row[table_details['columns'].index('action')] == 'connect') and (row[table_details['columns'].index('family')] == '2') and (row[table_details['columns'].index('type')] == '2') and (row[table_details['columns'].index('remote_address')] == '169.254.169.254') and (row[table_details['columns'].index('is_container_process')] == '1'):
                            socket_events['socket_events_3_alert-builder-added'] += 1
                            #socket_events['socket_events_1_alert-builder-added'] += 1
                        if (row[table_details['columns'].index('action')] == 'connect') and (row[table_details['columns'].index('cmdline')] == '-e') and (row[table_details['columns'].index('path')] == '/usr/bin/ruby'):
                            socket_events['socket_events_4_alert-builder-added'] += 1
                            socket_events['socket_events_1_alert-builder-added'] += 1
                        if "9.5.4.3" in row[table_details['columns'].index('remote_address')] or "169.254.169.254" in row[table_details['columns'].index('remote_address')]:
                            socket_events['socket_events_5_alert-builder-added'] += 1
                        if "malware" in row[table_details['columns'].index('remote_address')]:
                            socket_events['socket_events_6_alert-builder-added'] += 1
                if table_details['name'] == 'process_file_events':
                    rows = table_details['rows']
                    for row in rows:
                        if (row[table_details['columns'].index('path')] == '/etc/passwd') and (row[table_details['columns'].index('operation')] == 'open') and (row[table_details['columns'].index('flags')] == 'O_WRONLY'):
                            process_file_events['process_file_events_3_alert-builder-added'] += 1
                            process_file_events['process_file_events_4_alert-builder-added'] += 1
                        if (row[table_details['columns'].index('operation')] == 'chmod') and (row[table_details['columns'].index('flags')] == 'S_ISUID'):
                            process_file_events['process_file_events_alert-builder-added'] += 1
                        if (row[table_details['columns'].index('operation')] == 'rename') and (row[table_details['columns'].index('dest_path')] == '/.'):
                            process_file_events['process_file_events_5_alert-builder-added'] += 1
                        if row[table_details['columns'].index('operation')] == 'chown32':
                            process_file_events['process_file_events_6_alert-builder-added'] += 1
                        if (row[table_details['columns'].index('operation')] == 'write') and (row[table_details['columns'].index('executable')] == 'System') and (('.exe' in row[table_details['columns'].index('path')]) or ('4D5A9000' in row[table_details['columns'].index('magic_number')])):
                            process_file_events['process_file_events_7_alert-builder-added'] += 1
                        if (row[table_details['columns'].index('operation')] == 'rename'):
                            process_file_events['process_file_events_8_alert-builder-added'] += 1
                        if ('/etc/ld.so.conf' in row[table_details['columns'].index('path')]) and (row[table_details['columns'].index('operation')] == 'open') and (row[table_details['columns'].index('flags')] == 'O_WRONLY'):
                            process_file_events['process_file_events_9_alert-builder-added'] += 1
                        if (row[table_details['columns'].index('path')] == '/etc/passwd') and (row[table_details['columns'].index('operation')] == 'open') and (row[table_details['columns'].index('is_container_process')] == '0'):
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
    print((sum(dict1.values()))*126)
