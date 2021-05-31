from data_model.service_runtime import ServiceRuntime
from gevent import lock
from typing import List, Callable, Optional
from core_runtime.service_runner.status_code import StatusCode
from core_runtime.lifetime_controller.lifetime_controller import LifetimeContoller


class ServiceContainer(object):

    def __init__(self, service_runtime: ServiceRuntime = None, service_id: str = ""):
        # inner objects
        self.service_runtime = service_runtime
        self.service_id = service_id

        # service container state
        self.state: Optional[StatusCode] = None
        self.message = ""

        # lock
        self.service_container_lock = lock.BoundedSemaphore()
        self.in_running_lock = lock.BoundedSemaphore()
        self.snapshot_lock = lock.BoundedSemaphore()

        # for terminated
        self.should_terminated_flag = False
        self.terminate_done = False

        # hold this lock for the lifetime of this container
        # once the snapshot need to be take,it will block the request until
        # container release it
        self.snapshot_lock.acquire()
        # snapshot flag is for testing if the service is terminated for snapshot
        self.snapshot_flag = False
        # release the lock until current service is done
        # using for sync service request
        self.in_running_lock.acquire()

        # call backs for service done
        self.callbacks: List[Callable] = []

    def terminate_service(self):
        '''
            terminate current service after current function
        '''
        self.service_container_lock.acquire()
        self.should_terminated_flag = True
        self.service_container_lock.release()

    def take_snapshot(self):
        '''
            sync, service is terminated when this call returns
            we can safely store it's info 
        '''
        # set snapshot flag
        self.service_container_lock.acquire()
        self.snapshot_flag = True
        self.service_container_lock.release()

        # terminate the service
        self.terminate_service()
        # block caller until cna take_snapshot
        self.snapshot_lock.acquire()

    def get_snapshot_flag(self):
        self.service_container_lock.acquire()
        flag = self.snapshot_flag
        self.service_container_lock.release()
        return flag

    def check_if_service_terminated(self):
        '''
            check for runner, each time , it should check if
            the service is terminated, if it is, stop running it
        '''
        self.service_container_lock.acquire()
        check = False
        if self.should_terminated_flag == True:
            check = True
        self.service_container_lock.release()
        return check

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def do_callback(self):
        '''
            do things when this service is done 
            currently, we use it the sending messages, such as 
            snapshot, running state, and lifetime controll if this service is terminated
        '''
        if self.service_runtime.service.is_realtime == False:
            LifetimeContoller.manually_warmup_services(
                self.service_runtime.service, replica_diff=-1)

        self.in_running_lock.release()
        self.snapshot_lock.release()
        for func in self.callbacks:
            if func is not None:
                func()

    def sync_waiting_done(self):
        self.in_running_lock.acquire()
