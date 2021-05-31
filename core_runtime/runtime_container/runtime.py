# runtime 需要有啥

# service waiting queue
# check point request function, add tag for the (user, service) tuple

# runtime 有一个class ，runtime lock用来锁runtime，
# service in-running map {id: serviceRuntime}
# service done map {id: serviceRuntime}
# user-id: service-token map
# 其他类：
# service-token-generator: 生成唯一的service-tocken后开始执行代码
# service-runner，使用锁进行同步操作， 获取对象进行执行

from typing import Dict, List, Set, Type, Tuple, Optional
from gevent import lock, spawn, pool
from enum import Enum

from data_model.service_runtime import ServiceRuntime
from data_model.service import Service, Function
from core_runtime.runtime_container.service_container import ServiceContainer
from core_runtime.lifetime_controller.lifetime_controller import LifetimeContoller


from core_runtime.runtime_container.token_manager import TokenManager
# ! we implement a serial runner at first
from core_runtime.service_runner.DAG_runner.service_runner import ServiceRunner
from core_runtime.service_runner.status_code import StatusCode


class RuntimeError(object):
    def __init__(self, message):
        self.message = message


class ETryAgain(RuntimeError):
    def __init__(self, message):
        self.message = message


class ServiceType(Enum):
    snapshot_restore = 1
    new_run = 2


class Runtime(object):
    # lock for the runtime, in case of concurrent access
    _runtime_lock = lock.BoundedSemaphore()

    # other private class
    runner = ServiceRunner()
    # token mannagers for user and service
    # generate unique token, and returns to user
    service_token_generator = TokenManager()
    user_token_generator = TokenManager()

    # runtime data objects
    service_in_running_map: Dict[str, ServiceContainer] = {}
    service_done_map: Dict[str, ServiceContainer] = {}
    user_service_map: Dict[str, Set[str]] = {}

    @classmethod
    def _spawn_async_worker(cls, user_id: str,
                            service_id: str,
                            service: ServiceRuntime,
                            run_type: ServiceType = ServiceType.new_run):
        # use gevent spawn to spawn a greenlet worker
        spawn(cls._runner_warpper,
              user_id, service_id, service, run_type)

    @classmethod
    def _runner_warpper(cls, user_id: str,
                        service_id: str,
                        service: ServiceRuntime,
                        run_type: ServiceType = ServiceType.new_run):
        # add service into user_service_map and in running map
        service_container = ServiceContainer(service, service_id)
        cls._runtime_lock.acquire()
        # user_service_map
        if user_id not in cls.user_service_map:
            cls.user_service_map[user_id] = {service_id}
        else:
            cls.user_service_map[user_id].add(service_id)
        # put service in running map
        cls.service_in_running_map[service_id] = service_container
        cls._runtime_lock.release()

        # add point for lifetime controller
        # warmup function for none-realtime services
        if service.service.is_realtime == False:
            LifetimeContoller.manually_warmup_services(
                service.service, replica_diff=1)

        # begin run
        status, err = None, None
        if run_type == ServiceType.new_run:
            status, err = cls.runner.new_run(service_container, None)
        elif run_type == ServiceType.snapshot_restore:
            status, err = cls.runner.restore_run(service_container, None)
        else:
            status, err = None, "Unknown service type"

        # put status into container
        service_container.state = status

        # put err msg into container
        if err == None:
            service_container.message = ""
        else:
            service_container.message = err

        # service done running, move to done
        cls._runtime_lock.acquire()
        cls.service_in_running_map.pop(service_id)
        cls.service_done_map[service_id] = service_container
        cls._runtime_lock.release()

    @classmethod
    def _user_post_info_validation(cls, user_id: str, service_id: str) -> Optional[RuntimeError]:
        error = None
        if user_id not in cls.user_service_map:
            error = RuntimeError("user not found")
        if error == None and service_id not in cls.user_service_map[user_id]:
            error = RuntimeError("user didn't request such service")
        if error == None and ((service_id not in cls.service_in_running_map) and
                              (service_id not in cls.service_done_map)):
            error = RuntimeError("internal error, service missing in runtime")
        return error

    @classmethod
    def validate_user_id(cls, user_id: str) -> bool:
        if user_id not in cls.user_service_map:
            return False
        else:
            return True

    @classmethod
    def snapshot(cls, user_id: str, service_id: str) -> Tuple[
            Optional[ServiceRuntime], Optional[RuntimeError]]:
        error = cls._user_post_info_validation(user_id, service_id)
        if error is not None:
            return None, error

        ret: Optional[ServiceContainer] = None
        cls._runtime_lock.acquire()

        # there is two conditions right now
        if service_id in cls.service_in_running_map:
            ret = cls.service_in_running_map[service_id]
            # temporarily release the lock
            cls._runtime_lock.release()
            # call take snapshot to get the snapshot point
            # using lock in service context to synchronize snapshot
            ret.take_snapshot()
            # acquire this lock back
            cls._runtime_lock.acquire()

        # in service done map
        if service_id in cls.service_done_map:
            ret = cls.service_done_map[service_id]

        # release for all conditions
        cls._runtime_lock.release()

        # try to remove the service
        # this function require lock, make sure we release it
        is_removed, err = cls.remove_service(user_id, service_id)
        if is_removed == False:
            return None, err

        return ret.service_runtime, None

    @classmethod
    def restore_snapshot(cls, user_id: str, service: ServiceRuntime) -> Tuple[
            Optional[str], Optional[RuntimeError]]:
        return cls._run_service(user_id, service, ServiceType.snapshot_restore)

    @classmethod
    def run_new_service(cls, user_id: str, service: ServiceRuntime) -> Tuple[
            Optional[str], Optional[RuntimeError]]:
        return cls._run_service(user_id, service, ServiceType.new_run)

    @classmethod
    def _run_service(cls, user_id: str,
                     service: ServiceRuntime,
                     run_type: ServiceType = ServiceType.new_run) -> Tuple[
            Optional[str], Optional[RuntimeError]]:

        if cls.validate_user_id(user_id) == False:
            return None, RuntimeError('Invalid user id')

        service_token = cls.service_token_generator.gen_token()
        cls._spawn_async_worker(user_id, service_token, service, run_type)
        return service_token, None

    @classmethod
    def async_get_service_result(cls, user_id: str, service_id: str) -> Tuple[
            Optional[ServiceRuntime],  Optional[RuntimeError]]:

        error = cls._user_post_info_validation(user_id, service_id)
        if error is not None:
            return None, error

        service_container: Optional[ServiceContainer] = None
        cls._runtime_lock.acquire()
        if service_id in cls.service_in_running_map:
            service_container = None
        if service_id in cls.service_done_map:
            service_container = cls.service_done_map[service_id]
        cls._runtime_lock.release()

        if service_container is None:
            return None, ETryAgain("service_container is None")

        if service_container.state != StatusCode.success:
            cls.remove_service(user_id, service_id)
            return None, RuntimeError("running failed: %s" % service_container.message)

        cls.remove_service(user_id, service_id)
        return service_container.service_runtime, None

    @ classmethod
    def sync_get_service_result(cls, user_id: str, service_id: str):
        error = cls._user_post_info_validation(user_id, service_id)
        if error is not None:
            return None, error

        service_container: Optional[ServiceContainer] = None
        cls._runtime_lock.acquire()
        if service_id in cls.service_in_running_map:
            service_container = cls.service_in_running_map[service_id]
            # sync waiting done
            cls._runtime_lock.release()
            service_container.sync_waiting_done()
            cls._runtime_lock.acquire()

        elif service_id in cls.service_done_map:
            service_container = cls.service_done_map[service_id]
        cls._runtime_lock.release()

        if service_container is None:
            cls.remove_service(user_id, service_id)
            return None, RuntimeError("internal error, service_container is None")

        if service_container.state != StatusCode.success:
            cls.remove_service(user_id, service_id)
            return None, RuntimeError("running failed: %s" % service_container.message)

        cls.remove_service(user_id, service_id)
        return service_container.service_runtime, None

    @ classmethod
    def remove_service(cls, user_id: str, service_id: str) -> Tuple[
            bool, Optional[RuntimeError]]:
        error = cls._user_post_info_validation(user_id, service_id)
        if error is not None:
            return False, error
        else:
            cls._runtime_lock.acquire()
            cls.user_service_map[user_id].remove(service_id)
            if service_id in cls.service_in_running_map:
                # temporary release this lock as multiple lock would be acquired
                cls._runtime_lock.release()
                cls.service_in_running_map[service_id].terminate_service()
                # out of CS, acquire lock again
                cls._runtime_lock.acquire()
                cls.service_in_running_map.pop(service_id)
            if service_id in cls.service_done_map:
                cls.service_done_map.pop(service_id)
            cls._runtime_lock.release()
            cls.service_token_generator.destroy_token(service_id)
            return True, None

    @ classmethod
    def add_user(cls, user_info: Optional[Dict]):
        # current NotImplemented user_info
        user_token = cls.user_token_generator.gen_token()

        cls._runtime_lock.acquire()
        cls.user_service_map[user_token] = set()
        cls._runtime_lock.release()

        return user_token

    @ classmethod
    def destroy_user(cls, user_token: str):
        # remove all services
        if user_token in cls.user_service_map:
            for service_token in cls.user_service_map[user_token]:
                cls.remove_service(user_token, service_token)
                cls._runtime_lock.acquire()
                cls.user_service_map[user_token].remove(service_token)
                cls._runtime_lock.release()
            cls._runtime_lock.acquire()
            cls.user_service_map.pop(user_token)
            cls._runtime_lock.release()

    @ classmethod
    def remove_user(cls, user_token: str):
        cls.destroy_user(user_token)
        cls.user_token_generator.destroy_token(user_token)
