import logging
import os
from flask import Flask
from flask import jsonify
from ping3 import ping
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)

if not os.path.exists('data'):
    os.makedirs('data')
app = Flask(__name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s: line number:%(lineno)d')

file_handler = logging.FileHandler('panoptes.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class LimitExceed(Exception):
    status_code = 410

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class InternalServer(Exception):
    status_code = 500

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(LimitExceed)
def handle_limit_exceed(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(InternalServer)
def handle_limit_exceed(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(500)
def internal_error(error):
    return "Internal server error", 500


@app.route('/')
def index():
    return 'Hello'


def get_hosts():
    file = open('servers', 'r')
    lines = file.readlines()
    file.close()
    # Strips the newline character
    lines = [line.strip() for line in lines]
    return lines


def get_host_ping(host):
    return host, ping(host,timeout=1)


@app.route('/pings', methods=['GET'])
def ping_server():
    try:
        hosts_pings={}
        result = executor.map(get_host_ping, get_hosts())
        for (host,value) in result:
            hosts_pings[host]=value
        #hosts_pings = { host: value for (host,value) in result}
        return jsonify(hosts_pings)
    except InvalidUsage as err:
        logger.exception(err)
        raise InvalidUsage(err.message, status_code=400)
    except LimitExceed as err:
        logger.exception(err)
        raise LimitExceed(err.message, status_code=410)
    except Exception as err:
        logger.exception(err)
        raise InternalServer("Internal Server Error", status_code=500)


@app.route('/hosts', methods=['GET'])
def hosts():
    try:
        return jsonify(get_hosts())
    except InvalidUsage as err:
        logger.exception(err)
        raise InvalidUsage(err.message, status_code=400)
    except LimitExceed as err:
        logger.exception(err)
        raise LimitExceed(err.message, status_code=410)
    except Exception as err:
        logger.exception(err)
        raise InternalServer("Internal Server Error", status_code=500)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
