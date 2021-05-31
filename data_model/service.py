from typing import Dict,  List
import toposort
#! 预计当前模型可支持两种model
#  DAG model 与 线性 model
#  DAG model 目前需要进一步进行算法验证等工作，暂时处于设想阶段，暂时不实现


class Function(object):
    '''
        Function model , it is the node of the DAG
        A function has :
        1. function name, which is the same as the faas function name
        2. function tag, which is the unique identifier for the service
        3. list of next function, which is the function tag of the next functions
        we can use it to walk the DAG graph

        more info: we need the depend-on list of functions,
        only the depend-on functions are processed, current function can be
        process then
        SO, THIS
    '''

    def __init__(self, name: str,
                 function_id: int = 0):
        self.name = name
        self.function_id = function_id


class Service(object):
    '''
        Service model for add service to system
        A service has :
        1. name
        2. first_function is the first node of the DAG graph
        using function tag to identify the first node
            0 by default
        3. function_dict
    '''

    def __init__(self, name=None,
                 first_function: int = 0,
                 function_dict: Dict[int, List[int]] = {},
                 function_list: List[Function] = [],
                 is_realtime: bool = False):
        self.name = name
        self.first_function = first_function
        self.function_dict = function_dict

        self.function_list = function_list
        self.is_realtime = is_realtime

        self.topo_queue: List[int] = []
        self.pre_function: Dict[int, List[int]] = {}
        self.function_info: Dict[int, Function] = {}
        # parse graph
        try:
            function_dict_tmp = {}
            for k, v in self.function_dict.items():
                for i in v:
                    if i not in self.pre_function:
                        self.pre_function[i] = []
                    self.pre_function[i].append(k)

            for k, v in self.pre_function.items():
                function_dict_tmp[k] = set(v)

            self.topo_queue = list(
                toposort.toposort_flatten(
                    function_dict_tmp, sort=True))
            if (len(self.topo_queue) != 0 and
                    self.first_function != self.topo_queue[0]):
                raise Exception((
                    "DAG wrong define, first function is: %d not equal with topo queue: %s first element") % (
                        self.first_function, str(self.topo_queue))
                )

            for func in function_list:
                self.function_info[func.function_id] = func

            # for debug
            # print(self.topo_queue,self.pre_function,self.function_info)
        except Exception as e:
            raise Exception("parse topo graph failed: %s" % str(e))
