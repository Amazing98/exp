
from typing import Dict
from data_model.service import Service, Function
from gevent import lock
from core_runtime.faas_sub_sys.faas import FaasSubSys as FaaSClient
from config.conf import ServerConfig


class LifetimeContoller():

    # lock for this class
    lifetime_controller_lock = lock.BoundedSemaphore()
    # lock for record services state
    realtime_services: Dict[str, int] = {}
    # lock for record function state
    functions_ref_count: Dict[str, int] = {}

    @classmethod
    def add_realtime_services(cls, service: Service, replica_cnt: int = 1):
        if ServerConfig.life_controller_on == False:
            return True, "life_controller_on ==False"

        if replica_cnt <= 0:
            return False, "replica should > 0"
        with cls.lifetime_controller_lock:
            if service.name not in cls.realtime_services:
                cls.realtime_services[service.name] = replica_cnt
            else:
                cls.realtime_services[service.name] = cls.realtime_services[service.name] + replica_cnt
        return cls.scaling_service(service, replica_cnt)

    @classmethod
    def remove_realtime_services(cls, service: Service, replica_cnt: int = 1):
        if ServerConfig.life_controller_on == False:
            return True, "life_controller_on ==False"

        if replica_cnt <= 0:
            return False, "replica should > 0"
        with cls.lifetime_controller_lock:
            if service.name not in cls.realtime_services:
                return True, ""
            if cls.realtime_services[service.name] <= replica_cnt:
                del cls.realtime_services[service.name]
            else:
                cls.realtime_services[service.name] = cls.realtime_services[service.name] - replica_cnt
        return cls.scaling_service(service, -replica_cnt)

    # duration sec is not implemented right now
    # replica_diff can be negative, if so, down scale replica_diff numbers of functions
    @classmethod
    def manually_warmup_services(cls, service: Service, replica_diff: int = 1, duration_sec: int = -1):
        if ServerConfig.life_controller_on == False:
            return True, "life_controller_on ==False"

        return cls.scaling_service(service, replica_diff)

    # replica_diff can be negative, if so, down scale replica_diff numbers of functions
    # TODO: using success set to rolling back ,make this function as automatic
    @classmethod
    def scaling_service(cls, service: Service, replica_diff: int):
        if ServerConfig.life_controller_on == False:
            return True, "life_controller_on ==False"

        success_set = set()  # for rolling back
        for function in service.function_list:
            replica = 0
            if function.name in cls.functions_ref_count:
                replica = cls.functions_ref_count[function.name] + replica_diff
            # should not be
            if replica < 0:
                replica = 0

            ok, err = FaaSClient.scaling_function(
                function.name, replica_num=replica)
            if ok == False:
                # TODO: using success set to rolling back ,make this function as automatic
                return ok, err

            # post records
            success_set.add(function.name)
            with cls.lifetime_controller_lock:
                cls.functions_ref_count[function.name] = replica
                if replica == 0 and (function.name in cls.functions_ref_count):
                    del cls.functions_ref_count[function.name]

        return True, ""
    # TODO : using service state to calibrate function state
