from config.conf import ServerConfig
from routes import init_app
import sys
from flask import request
from flask import Flask
from gevent.pywsgi import WSGIServer
from gevent import monkey
monkey.patch_all()


app = Flask(__name__)


@app.route("/", methods=['POST'])
def home():
    msg = request.get_data()
    return "repeated from wrapper " + str(msg)


if __name__ == "__main__":
    init_app(app)
    app.run(ServerConfig.server_ip, ServerConfig.server_port, debug=True)
    # http_server = WSGIServer(('0.0.0.0', 5050), app)
    # http_server.serve_forever()
