from gevent import lock
from typing import Set
import secrets


class TokenManager(object):

    def __init__(self):
        self.token_manager_lock = lock.BoundedSemaphore()
        self.current_token: Set = set()

    def gen_token(self):
        token = secrets.token_urlsafe(32)
        self.token_manager_lock.acquire()
        self.current_token.add(token)
        self.token_manager_lock.release()
        return token

    '''
        @return True if success
        @return False if failed
    '''

    def destroy_token(self, token: str):
        if token not in self.current_token:
            return False
        else:
            self.token_manager_lock.acquire()
            self.current_token.remove(token)
            self.token_manager_lock.release()
            return True
