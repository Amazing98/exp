from gevent.subprocess import Popen, PIPE
from typing import Set, Dict
from config.conf import FaaSConfig as Config
from .docker_client import DockerClient
from data_model.service import Function
import requests


class FaasSubSys(object):
    function_set: Set[str] = set()

    @classmethod
    def get_faas_func_list(cls):
        popen = Popen(
            [Config.fass_cli_position, "list"], stdout=PIPE)
        out, err = popen.communicate()
        if err is not None:
            return err

        function_set: Set[str] = set()
        output_str = out.decode("utf-8")
        lines = output_str.split("\n")
        for line in lines[1:-1]:
            function_set.add(line.split("\t")[0].strip())
        cls.function_set = function_set
        return None

    @classmethod
    def function_dict_validate(cls, function_dict: Dict[int, Function]):
        invalid_list = []
        try:
            for _, function in function_dict:
                if function not in cls.function_set:
                    invalid_list.append(function)
        except:
            return False, None

        if len(invalid_list) == 0:
            return True, None
        else:
            return False, invalid_list

    @classmethod
    def if_login_test(cls):
        popen = Popen(
            [Config.fass_cli_position, "list"], stdout=PIPE)
        out, err = popen.communicate()
        if err is not None:
            return False

        output_str = out.decode("utf-8")
        if "Unauthorized access" in output_str:
            return False
        else:
            return True

    @classmethod
    def faas_path_validate(cls):
        try:
            popen = Popen(
                [Config.fass_cli_position], stdout=PIPE)
            out, err = popen.communicate()
        except:
            return False

        if err is not None:
            return False

        output_str = out.decode("utf-8")
        if "Manage your OpenFaaS functions from the command line" in output_str:
            return True
        else:
            return False

    @classmethod
    def faas_login(cls):
        popen = Popen(
            [Config.fass_cli_position,
             "login",
             "--username", Config.fass_username,
             "--password", Config.fass_password,
             "--gateway", "http://"+Config.faas_ip+":"+str(Config.faas_port)],
            stdout=PIPE)
        out, err = popen.communicate()
        if err is not None:
            return False

        output_str = out.decode("utf-8")
        if "credentials saved" in output_str:
            return True
        else:
            return False

    @classmethod
    def deploy_function(cls, image_name: str, function_name: str) -> bool:
        if DockerClient.init_app() == False:
            return False
        if DockerClient.check_image_name(image_name) == False:
            return False

        if function_name is None or function_name == "":
            deploy_function_name = image_name

        popen = Popen(
            [Config.fass_cli_position,
             "deploy",
             "--image", image_name,
             "--name", deploy_function_name],
            stdout=PIPE)
        out, err = popen.communicate()
        if err is not None:
            return False

        output_str = out.decode("utf-8")
        if "Deployed. 202 Accepted." in output_str:
            return True
        else:
            return False

    @classmethod
    def remove_function(cls, function_name: str) -> bool:
        popen = Popen(
            [Config.fass_cli_position,
             "remove", function_name],
            stdout=PIPE)
        out, err = popen.communicate()
        if err is not None:
            return False

        output_str = out.decode("utf-8")
        if "Removing old function." in output_str:
            return True
        else:
            return False

    # this function sets this function's replica to replica_num
    @classmethod
    def scaling_function(cls, function_name: str, replica_num: int):
        request_url = "http://" + Config.faas_ip + ":" + \
            str(Config.faas_port) + \
            "/system/scale-function/" + function_name
        header = {
            "Authorization": "Basic "+Config.faas_basic_auth().decode("utf-8")[:-1]
        }
        json = {
            "service": function_name,
            "replicas": replica_num
        }

        res = requests.post(url=request_url, headers=header, json=json)

        if res.status_code != 200 and res.status_code != 202:
            return False, "request failed, status code is %d" % res.status_code
        return True, ""
