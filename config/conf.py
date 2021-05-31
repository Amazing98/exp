import requests
import base64


class FaaSConfig(object):
    '''
        faas config is the config of open-faas environment
    '''
    faas_ip = "127.0.0.1"
    faas_port = 31112
    fass_username = "admin"
    # for k8s, you can use the underlay command to get password:
    # echo $(kubectl -n openfaas get secret basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode)
    fass_password = "F3JnwN0HpcNF"
    fass_cli_position = "core_runtime/faas_sub_sys/faas-cli"

    # get basic auth for call RESTful APIs
    # needs header "Authorization":" Basic <your token here>"
    # exp:curl http://127.0.0.1:31112/system/functions -H "Authorization: Basic YWRtaW46RjNKbndOMEhwY05G"

    @classmethod
    def faas_basic_auth(cls) -> bytes:
        tmp = (cls.fass_username + ":" + cls.fass_password).encode()
        return base64.encodebytes(tmp)


class ServerConfig(object):
    '''
        server config is the config for service
        which port and ip should be used
    '''
    server_ip = "0.0.0.0"
    server_port = 5050
    life_controller_on = False
