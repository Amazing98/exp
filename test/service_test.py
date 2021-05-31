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
    	"1":[]
    },
    "function_list":[
        {
            "name":"echo-py",
            "function_id":1
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
    "http://127.0.0.1:5050/user_request/new_service/%s/test" % user_token, json=json.loads('''{"data":"nihao"}'''))

if service_req_res.status_code != 200:
    print("request failed, status code:%d , text is %s" %
          (service_req_res.status_code, service_req_res.text))
    exit()

service_token = service_req_res.json()["service_token"]
if len(service_token) == 0:
    print("service token length wrong \n")
    exit()
print("service_token is: %s" % service_token)


# request result for user
time.sleep(1)
res = requests.get("http://127.0.0.1:5050/user_request/async/%s/%s" %
                   (user_token, service_token))
print("res.status_code: %d, res.text: %s" % (res.status_code, res.text))
