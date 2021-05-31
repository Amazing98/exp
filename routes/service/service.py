from flask import Blueprint, request, jsonify
from data_model import Function, Service, schemaFunc, schemaServ
from core_runtime.service_manager.service_manager import RegistedService
service_route = Blueprint('service_manage', __name__)

# 使用json来增删查改对应函数，在增删过程中会检查对应服务名是否已有定义
# 服务json定义如下，为实现DAG格式
# {
#     "name":"test",
#     "first_function":1,
#     "function_dict":{
#         "1":[2,3],
#         "2":[4],
#         "3":[4],
#     },
#     "function_list":[
#         {
#             "name":"add1",
#             "function_id":1
#         },
#         {
#             "name":"add1",
#             "function_id":2
#         },
#         {
#             "name":"add1",
#             "function_id":3
#         },
#         {
#             "name":"add1",
#             "function_id":4
#         }
#     ]
# }


@service_route.route('/<service_name>', methods=['GET'])
def get_service_info(service_name: str):
    try:
        if service_name not in RegistedService:
            raise Exception("service not registed")

        service = RegistedService[service_name]
        try:
            return jsonify(schemaServ.dump(service)), 200
        except:
            raise Exception("internal error: service can not be dumped")

    except Exception as e:
        return jsonify("request failed: %s" % e.__str__()), 500


@service_route.route('/<service_name>', methods=['POST'])
def post_new_service(service_name: str):
    try:

        try:
            new_service = schemaServ.load(request.json)
        except Exception as e:
            raise Exception("not a valid json: %s" % str(e))

        if new_service.name != service_name:
            raise Exception("service name should encoded at url")

        if new_service.name not in RegistedService:
            RegistedService[new_service.name] = new_service
        else:
            raise Exception("Service already exists")

        return jsonify("success"), 200
    except Exception as e:
        return jsonify("request failed: %s" % e.__str__()), 500


@service_route.route('/<service_name>', methods=['DELETE'])
def delete_old_service(service_name: str):
    if service_name not in RegistedService:
        return jsonify("service not registed"), 404
    else:
        del RegistedService[service_name]
        return jsonify("success"), 200


@service_route.route('/<service_name>', methods=['UPDATE'])
def update_old_service(service_name: str):
    try:
        try:
            new_service = schemaServ.load(request.json)
        except:
            raise Exception("not a valid json")

        if new_service.name in RegistedService:
            del RegistedService[new_service.name]
            RegistedService[new_service.name] = new_service
        else:
            raise Exception("Service did't exists")

        return jsonify("success"), 200
    except Exception as e:
        return jsonify("request failed: %s" % e.__str__()), 500
