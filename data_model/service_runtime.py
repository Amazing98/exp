from data_model.service import Service
from marshmallow.fields import Raw
from typing import List, Dict, Tuple

#! this file implement the  model of service runtime
#! currently, only serial model is supported: len(FunctionRuntime.next) should be equal to 1

'''
    this file is for the service runtime:
    - every service has multiple functions, each functions has their previous
    functions, which would form a serail
    - each functions has a unique tag:Int as offset
    - runtime performs functions follow this tag number
    - as function has been performed, it's result will be recorded in FunctionInput
      which also ref by tag number
    - runtime performs function in single threaded(didn't forbid in function thread,
      just no need to)

    - ServiceRuntime : logs the current offset, and strores multiple function runtimes
    - FunctionRuntime : since function has multiple next functions, it stores it's output
      until no function is ref to it, once a function is used it's data, it will remove it
      from list, when the function list is empty, data will be deleted
'''


class DataContainer(object):
    def __init__(self, data: str, ref_cnt: int):
        self.data = data
        self.ref_cnt = ref_cnt

    def de_ref(self):
        '''
            de-ref is called by other function
            if other function is processed
            this function data is no need for them
            de-ref to zero is for this data is  no more needed
            we can clean up this data
        '''
        if self.ref_cnt == 0:
            return

        self.ref_cnt -= 1
        if self.ref_cnt == 0:
            del self.data
            self.data = None
        return


class ServiceState(object):
    def __init__(self,
                 service_queue: List[int] = [],
                 service_data: Dict[int, DataContainer] = {},
                 service_input_data: str = "",
                 service_output_data: str = ""):
        # a Tuple[int,int], first is the cur_node,second is the prev_node
        self.service_queue = service_queue
        self.service_data = service_data

        # user data input,should destroy after first_function finish
        self.service_input_data = service_input_data
        # if we compute the last function, put it's data here
        self.service_output_data = service_output_data


class ServiceRuntime(object):
    '''
    class ServiceRuntime is the container of executing service
    we define the service as a DAG function 
    we executing every function using the BFS algorithm
    '''

    def __init__(self,
                 service: Service = None,
                 service_state: ServiceState = None):
        self.service = service
        self.service_state = service_state
