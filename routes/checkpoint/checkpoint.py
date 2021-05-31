from flask import Blueprint, request, jsonify, send_file, make_response
from core_runtime.runtime_container.runtime import Runtime
from core_runtime.snapshot.snapshot import SnapshotController
from io import BytesIO

checkpoint = Blueprint('checkpoint', __name__)


@checkpoint.route('/restore/<user_id>', methods=['POST'])
def restore_checkpoint(user_id: str):
    if Runtime.validate_user_id(user_id) == False:
        return jsonify({"error": "invalid user id"}), 500

    if len(request.files) != 1:
        return jsonify({
            "status": "error",
            "error": ("%d file has been uploaded, need one file" % len(request.files))
        }), 500

    file = None
    for v in request.files.values():
        file = v
    runtime_data = file.read()

    service_token, err = SnapshotController.run_snapshot(user_id,
                                                         runtime_data)
    if err is not None:
        return jsonify({
            "status": "error",
            "error": err.message
        }), 500

    return jsonify({
        "status": "success",
        "service_token": service_token
    }), 200


@ checkpoint.route('/save/<user_id>/<service_token>', methods=['GET'])
def save_checkpoint(user_id: str, service_token: str):
    snapshot, error = SnapshotController.take_snapshot(user_id, service_token)
    if error is not None:
        return jsonify({
            "status": "error",
            "error": error.message
        }), 404

    file_name = user_id+"."+service_token
    resp = make_response(send_file(BytesIO(snapshot),
                                   attachment_filename=file_name,
                                   as_attachment=True
                                   ), 200)
    resp.headers["Content-Disposition"] = "attachment; filename={}".format(
        file_name)

    return resp


@ checkpoint.route('/', methods=['DELETE', 'GET', 'POST', 'UPDATE'])
def not_found():
    return jsonify({'status': 404}), 404
