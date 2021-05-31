# deprecated

from core_runtime.runtime_container.service_container import ServiceContainer
from data_model.service_runtime import DataContainer
from data_model.service import Function
from typing import Tuple
import requests
from core_runtime.service_runner.status_code import StatusCode


class ServiceRunner(object):

    @classmethod
    def restore_run(cls, service: ServiceContainer, post_run_func: Function) -> Tuple[StatusCode, str]:
        return cls._run_serial(service, post_run_func)

    @classmethod
    def new_run(cls, service: ServiceContainer, post_run_func: Function) -> Tuple[StatusCode, str]:
        service.service_runtime.in_runing_queue.append(
            service.service_runtime.first_function)
        return cls._run_serial(service, post_run_func)

    @classmethod
    def _run_serial(cls, service: ServiceContainer, post_run_func: Function) -> Tuple[StatusCode, str]:
        runtime = service.service_runtime

        # iterator for function in DAG
        func_iter = None
        if_service_terminated = False

        # run until all serial functions are visited
        while (len(runtime.in_runing_queue) != 0):
            # check if we should stop processing for snapshot
            if_service_terminated = service.check_if_service_terminated()
            if if_service_terminated == True:
                break

            try:
                # get the first function
                # using the in running queue
                func_iter = runtime.function_runtime_map[
                    runtime.in_runing_queue[0]]
                # pop the head function of the list
                runtime.in_runing_queue = runtime.in_runing_queue[1:]
            except:
                return StatusCode.failed, ("tag %d not in function map" %
                                           runtime.in_runing_queue[0])

            # add the success functions to in_runing_queue
            for func in func_iter.next:
                runtime.in_runing_queue.append(func)

            depend_on_data = None
            if func_iter.tag == runtime.first_function:
                # for first function, use the user input data
                # this data will destroy after the function finish
                depend_on_data = runtime.service_input_data
            else:
                # serial service, depend-on has only one element
                if len(runtime.depend_on) == 1:
                    # ref depend_on_data
                    if func_iter.depend_on[0] in runtime.function_runtime_map:
                        depend_on_data = runtime.function_runtime_map[
                            func_iter.depend_on[0]].data
                    # error, not found
                    else:
                        return StatusCode.failed, ("func_iter.depend_on[0]: %d not found in runtime.function_runtime_map" %
                                                   func_iter.depend_on[0])
                # error, multiple function found
                else:
                    return StatusCode.failed, ("func_iter.depend_on has multiple elements,func_iter.tag: %d" %
                                               func_iter.tag)

            # TODO:add faas api gateway
            res = requests.post("", data=depend_on_data.data)
            # check for status code
            if res.status_code != 200:
                return StatusCode.failed, ("receive error status code : %d" %
                                           res.status_code)

            # de ref depend_on data
            depend_on_data.de_ref()

            # get raw data from requests
            # put data into data container
            if len(runtime.in_runing_queue) == 0:
                # there is no more functions will be executed
                # this is the last function
                # put data to output data container
                runtime.service_output_data = DataContainer(1, res.content)
            else:
                func_iter.data.data = res.content

        # call service finish when service is done
        # it will call at success and migrated state
        service.do_callback()

        if if_service_terminated == True:
            return StatusCode.migrated, None
        else:
            return StatusCode.success, None
