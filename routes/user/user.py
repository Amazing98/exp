from flask import Blueprint, request, jsonify
from core_runtime.runtime_container.runtime import Runtime

user_register = Blueprint('user', __name__)

'''
    user.py provide HTTP access for user register and deregister
    when a user want to access to this system,it should register first

    when register, it will return a token for the user
    the success request (request and checkpoint) should add this user_token to URI

'''


@user_register.route('/register', methods=['POST'])
def user_reg():
    token = Runtime.add_user(None)
    return jsonify({"token": token}), 200


@user_register.route('/deregister/<user_token>', methods=['GET'])
def user_deregister(user_token: str):
    if Runtime.validate_user_id(user_token) == False:
        return jsonify({"error": "Invalid user token"}), 500

    Runtime.remove_user(user_token)
    return jsonify({'success': True}), 200


@user_register.route('/', methods=['DELETE', 'GET', 'POST', 'UPDATE'])
def not_found():
    return jsonify({'status': 404}), 404
