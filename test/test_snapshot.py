import requests
import json
import time

# register user first
user_reg_res = requests.post(
    "http://127.0.0.1:5050/user/register", json="")

if user_reg_res.status_code != 200:
    print("register user failed\n")
    exit()

user_token = user_reg_res.json()["token"]

if len(user_token) == 0:
    print("user token length wronged\n")
    exit()

print("user register success, token: %s" % user_token)


# register a service
service_reg_res = requests.post("http://127.0.0.1:5050/manage/test", json=json.loads('''
{
    "name":"test",
    "first_function":1,
    "function_dict":{
        "1":[2,3],
        "2":[4],
        "3":[4],
        "4":[]
    },
    "function_list":[
        {
            "name":"add-1-delay",
            "function_id":1
        },        
        {
            "name":"add-1-delay",
            "function_id":2
        },        
        {
            "name":"add-1-delay",
            "function_id":3
        },        
        {
            "name":"add-1-delay",
            "function_id":4
        }
    ]
}'''))

if service_reg_res.status_code != 200:
    print("reg service failed,status code is: %d , text is %s" %
          (service_reg_res.status_code, service_reg_res.text))
    exit()

# if service_reg_res.text == "success":
print("register success: ", service_reg_res.text)


# request a service

service_req_res = requests.post(
    "http://127.0.0.1:5050/user_request/new_service/%s/test" % user_token, json=json.loads('''{"data":0}'''))

if service_req_res.status_code != 200:
    print("request failed, status code:%d , text is %s" %
          (service_req_res.status_code, service_req_res.text))
    exit()

service_token = service_req_res.json()["service_token"]
if len(service_token) == 0:
    print("service token length wrong \n")
    exit()
print("service_token is: %s" % service_token)


# request snapshot  for user
time.sleep(2)
print("begin take snapshot\n")
res = requests.get("http://127.0.0.1:5050/checkpoint/save/%s/%s" %
                   (user_token, service_token))
if res.status_code == 200:
    with open("./snapshot", "wb") as f:
        f.write(res.content)
    print("snapshot get success\n")
else:
    print("failed to get snapshot, res.status_code: %d, exiting ..." %
          (res.status_code))
    exit()


# test for snapshot
print("restore snapshot will begin after 5 sec...\n")
time.sleep(5)
print("begin restore snapshot\n")
snapshot_bin = None
files = {
    "field1": open("./snapshot", "rb")
}
r = requests.post("http://127.0.0.1:5050/checkpoint/restore/%s" %
                  (user_token),  files=files)
if r.status_code == 200:
    service_token = r.json()["service_token"]
    print("restore succuss, status_code is %d, new service token is %s" %
          (r.status_code, service_token))
else:
    print("restore failed, status_code is %d, reason is: %s" %
          (r.status_code,  r.json()["error"]))
    exit()

# request result for user(sync)
res = requests.get("http://127.0.0.1:5050/user_request/sync/%s/%s" %
                   (user_token, service_token))
print("res.status_code: %d, res.text: %s" % (res.status_code, res.text))
