from core_runtime.runtime_container.service_container import ServiceContainer
from data_model.service_runtime import DataContainer
from data_model.service import Function
from typing import Callable, List, Tuple, Optional
from config.conf import FaaSConfig
import requests
from core_runtime.service_runner.status_code import StatusCode

# !  python library <toposort> could be used in DAG service runner


class ServiceRunner(object):

    @classmethod
    def restore_run(cls, service: ServiceContainer, post_run_func: Optional[Function]) -> Tuple[StatusCode, str]:
        return cls._run_DAG(service, post_run_func)

    @classmethod
    def new_run(cls, service: ServiceContainer, post_run_func: Optional[Function]) -> Tuple[StatusCode, str]:
        return cls._run_DAG(service, post_run_func)

    @classmethod
    def _run_DAG(cls, service: ServiceContainer, post_run_func: Optional[Function]) -> Tuple[StatusCode, str]:
        # what to returns
        err_msg = ""
        status_code = None

        service_runtime = service.service_runtime

        # iterator for function in DAG
        func_iter = None
        if_service_terminated = False

        while(len(
                service_runtime.service_state.service_queue) != 0):

            # service terminate check
            if_service_terminated = service.check_if_service_terminated()
            if if_service_terminated == True:
                break

            func_iter = service_runtime.service_state.service_queue[0]
            service_runtime.service_state.service_queue = service_runtime.service_state.service_queue[
                1:]
            # this function is not refer by other function and is not the last one
            # skip
            if func_iter not in service_runtime.service.function_dict and len(
                    service_runtime.service_state.service_queue) != 0:
                continue

            # do exec
            try:
                function_name = service_runtime.service.function_info[func_iter].name
                previous_functions = []
                if func_iter in service_runtime.service.pre_function:
                    previous_functions = service_runtime.service.pre_function[func_iter]

                # marshal function data
                function_data = {"arg_num": 0,
                                 "args": {}}
                if func_iter == service_runtime.service.first_function:
                    function_data["arg_num"] = 1
                    function_data["args"]["input"] = service_runtime.service_state.service_input_data
                else:
                    function_data["arg_num"] = len(previous_functions)

                    for prev_func in previous_functions:
                        # raise exception if has any run-time error
                        if prev_func not in service_runtime.service_state.service_data:
                            raise Exception(
                                " can't find previous function %d data" % prev_func)
                        data = service_runtime.service_state.service_data[prev_func]
                        function_data["args"][str(prev_func)] = data.data
                        # data.de_ref()

                res = requests.post(
                    "http://" + FaaSConfig.faas_ip + ":" + str(FaaSConfig.faas_port) +
                    "/function/" + function_name,
                    json=function_data)

                # de-ref data
                if func_iter != service_runtime.service.first_function:
                    for prev_func in previous_functions:
                        data = service_runtime.service_state.service_data[prev_func]
                        data.de_ref()

                # check for status code
                if res.status_code != 200:
                    status_code = StatusCode.failed
                    err_msg = ("receive error status code : %d, res.text is %s" %
                               (res.status_code, res.text))
                    break

                # check for response schema
                res_json = res.json()
                if ("output" not in res_json) or ("status" not in res_json) or ("message" not in res_json):
                    status_code = StatusCode.failed
                    err_msg = "function %d returns schema is wrong" % func_iter
                    break

                if res_json["status"] != "True":
                    status_code = StatusCode.failed
                    err_msg = "running function %d has status code: %s, message is :%s" % (
                        func_iter,
                        res_json["status"],
                        res_json["message"])
                    break

                res_data = res_json["output"]

                if len(service_runtime.service_state.service_queue) == 0:
                    service_runtime.service_state.service_output_data = res_data
                    break
                else:
                    data = DataContainer(res_data, len(
                        service_runtime.service.function_dict[func_iter]))
                    service_runtime.service_state.service_data[func_iter] = data

            except Exception as e:
                status_code = StatusCode.failed
                err_msg = "service runner runtime: %s" % str(e)
                break

        # call service finish when service is done
        # it will call at success and migrated state
        service.do_callback()

        if status_code == None:
            if if_service_terminated == True:
                status_code = StatusCode.migrated
            else:
                status_code = StatusCode.success

        return status_code, err_msg
