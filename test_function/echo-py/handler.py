import json
from typing import Dict
# from typing import Dict


def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    res = {
        "output": "",
        "status": "True",
        "message": ""
    }

    req_obj = None
    try:
        req_obj = json.loads(req)
    except Exception as e:
        res["status"] = "False"
        res["message"] = "loads req failed: %s" % str(e)
        return json.dumps(res)

    if (not isinstance(req_obj, dict)) or ("args" not in req_obj) or ("arg_num" not in req_obj) or req_obj["arg_num"] != 1:
        res["status"] = "False"
        res["message"] = "req schema is wrong: %s" % req
        return json.dumps(res)

    try:
        for v in req_obj["args"].values():
            res["output"] = "Hello " + v
    except:
        res["status"] = "False"
        res["message"] = "running echo has internal error"
        return json.dumps(res)

    return json.dumps(res)
