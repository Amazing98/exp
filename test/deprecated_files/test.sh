curl -X POST -H "Content-Type: application/json" "http://127.0.0.1:5050/manage/test" -d '{
    "name":"test",
    "first_function":1,
    "function_dict":{
        "1":[2,3],
        "2":[4],
        "3":[4]
    },
    "function_list":[
        {
            "name":"add1",
            "function_id":1
        },        
        {
            "name":"add1",
            "function_id":2
        },        
        {
            "name":"add1",
            "function_id":3
        },        
        {
            "name":"add1",
            "function_id":4
        }
    ]
}'

curl -X POST -H "Content-Type: application/json" "http://127.0.0.1:5050/manage/test" -d '{
    "name":"test",
    "first_function":1,
    "function_dict":{
    },
    "function_list":[
        {
            "name":"echo-py",
            "function_id":1
        }
    ]
}'

curl "http://127.0.0.1:5050/manage/test" 