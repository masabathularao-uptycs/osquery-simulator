import time
import datetime
from datetime import datetime
import json
import jwt
import requests
import urllib3

def open_js_safely(file: str) -> dict:
    """Open a json file without leaving a dangling file descriptor"""
    with open(file, "r") as fin:
        content = fin.read()
    return json.loads(content)

def generateHeaders(key, secret):
    header = {}
    utcnow = datetime.utcnow()
    date = utcnow.strftime("%a, %d %b %Y %H:%M:%S GMT")
    exp_time = time.time() + 3600
    try:
        authVar = jwt.encode({'iss':key, 'exp': exp_time},secret).decode("utf-8")
    except:
        authVar = jwt.encode({'iss':key, 'exp': exp_time},secret)
    authorization="Bearer %s" % (authVar)
    header['date']=date
    header['authorization']=authorization
    header['Content-type']="application/json"
    return header

def realtime_query(api_key_file: str, query: str, hostname: str) -> dict:
    urllib3.disable_warnings()
    data = open_js_safely(api_key_file)
    headers = generateHeaders(data['key'], data['secret'])
    url = "https://%s.uptycs.io/public/api/customers/%s/queryJobs" % (data['domain'], data['customerId'])
    filters = {'live': True, 'hostName': hostname}
    raw_data = {'query': query, 'type':'realtime', 'filters': filters}
    json_payload = json.dumps(raw_data)
    resp = query_dialogue(data,url,json_payload,headers,120)
    #if resp.status_code != 200:
    #    raise Exception("Could not issue realtime query for api_key_file %s and query %s" % (api_key_file, query))
    #return resp.json()

def query_dialogue(data,url,json_payload,headers,timeout):
    t1= datetime.now()
    resp = requests.post(url, data=json_payload, headers=headers, verify=False, timeout=120)
    
    if resp.status_code == 200:
       query_output_post=json.loads(resp.text)
       if not 'status' in query_output_post.keys():
          resp.close()
          return resp
       if query_output_post['status'] == 'QUEUED':
          t2= datetime.now()
          if dif_in_miliseconds(t1,t2) > timeout*1000:
             resp.close()
             return resp
          pending_job_id=query_output_post.get('id')
          for cycle in range(50):
              url = "https://%s.uptycs.io/public/api/customers/%s/queryJobs/%s" % (data['domain'], data['customerId'],pending_job_id)
              t2= datetime.now()
              resp = requests.get(url, headers=headers, verify=False, timeout=timeout-dif_in_miliseconds(t1,t2)/1000)
              query_output=json.loads(resp.text)
              if query_output['status'] == 'ERROR':
                  print("query status is: %s, stats: %s" %(query_output['status'], query_output["queryJobAssetCounts"]))
                  time.sleep(10)
                  continue
              if query_output['status'] == 'QUEUED':
                  print("query status is: %s, stats: %s" %(query_output['status'], query_output["queryJobAssetCounts"]))
                  time.sleep(10)
                  continue
              if query_output['status'] == 'RUNNING':
                  print("query status is: %s, stats: %s" %(query_output['status'], query_output["queryJobAssetCounts"]))
                  time.sleep(10)
                  continue
              if query_output['status'] == 'FINISHED':
                  print("query status is: %s, stats: %s" %(query_output['status'], query_output["queryJobAssetCounts"]))
                  url = "https://%s.uptycs.io/public/api/customers/%s/queryJobs/%s/t1_result?limit=100" % (data['domain'], data['customerId'],pending_job_id)
                  t2= datetime.now()
                  resp = requests.get(url, headers=headers, verify=False, timeout=timeout-dif_in_miliseconds(t1,t2)/1000)
                  query_output=json.loads(resp.text)
                  resp.close()
                  return resp
       resp.close()
       return resp
    else:
       resp.close()
       return resp

def dif_in_miliseconds(t1, t2):
    dif = t2 - t1
    return int(dif.total_seconds()*1000)

if __name__ == "__main__":
    query = "select * from processes"
    hostname = "orange"
    api_key_file = '/home/donkey/go_http_real_time/go_http/api_config.json'
    print("performing realtime query for live assets with hostname: %s and query: %s" %(hostname,query))
    realtime_query(api_key_file=api_key_file, query=query, hostname=hostname)
    # print(resp)
