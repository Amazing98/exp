from flask import Blueprint, request, jsonify
from core_runtime.runtime_container.runtime import Runtime, ETryAgain, RuntimeError
from core_runtime.service_manager.service_manager import RegistedService
from data_model import schemaServRuntime
from data_model.service_runtime import ServiceRuntime, DataContainer, ServiceState

user_request = Blueprint('user_request', __name__)


@user_request.route('/new_service/<user_token>/<service_name>', methods=['POST'])
def add_new_service(user_token: str, service_name: str):
    if service_name not in RegistedService:
        return jsonify({'error': "service not registered"}), 404

    if Runtime.validate_user_id(user_token) == False:
        return jsonify({'error': "user not registered"}), 404

    service_metadata = RegistedService[service_name]
    if service_metadata.first_function not in service_metadata.function_dict:
        return jsonify({
            "status": "failed",
            "error":  "service metadata error"
        }), 500

    input_data = request.json
    print(input_data)
    if "data" not in input_data:
        return jsonify({
            "status": "failed",
            "error":  "input data error"
        }), 500
    service_state = ServiceState(
        service_metadata.topo_queue, {}, input_data["data"], "")

    service_runtime = ServiceRuntime(
        service_metadata,
        service_state)

    service_token, err = Runtime.run_new_service(user_token,
                                                 service_runtime)
    if err != None:
        return jsonify({
            "status": "failed",
            "error": err.message,
        }), 200
    return jsonify({
        "status": "success",
        "service_token": service_token
    }), 200


@user_request.route('/async/<user_token>/<service_token>', methods=['GET'])
def async_get_response(user_token: str, service_token: str):
    if Runtime.validate_user_id(user_token) == False:
        return jsonify({
            "status": "error",
            'error': "user not registered"}), 404

    runtime, err = Runtime.async_get_service_result(
        user_token, service_token)
    if err is not None:
        if isinstance(err, ETryAgain) == True:
            return jsonify({
                "status": "retry",
                "error": ""
            }), 500
        else:
            return jsonify({
                "status": "error",
                'error': err.message
            }), 500
    else:
        output = runtime.service_state.service_output_data
        del runtime
        return jsonify({
            "status": "success",
            "output": output
        }), 200


@user_request.route('/sync/<user_token>/<service_token>', methods=['GET'])
def sync_get_response(user_token: str, service_token: str):
    if Runtime.validate_user_id(user_token) == False:
        return jsonify({
            "status": "error",
            'error': "user not registered"
        }), 404

    runtime, err = Runtime.sync_get_service_result(
        user_token, service_token)
    if err is not None:
        return jsonify({
            "status": "error",
            'error': err.message
        }), 500
    else:
        output = runtime.service_state.service_output_data
        del runtime
        return jsonify({
            "status": "success",
            "output": output
        }), 200
    # return jsonify({"output": 4}), 200


@user_request.route('/', methods=['DELETE', 'GET', 'POST', 'UPDATE'])
def not_found():
    return jsonify({'status': 404}), 404
