from gevent.subprocess import Popen, PIPE
from typing import Set
import docker


class DockerClient(object):
    client = None
    image_names = set()

    @classmethod
    def init_app(cls):
        # init docker client
        if cls.client is None:
            try:
                cls.client = docker.from_env()
                return True
            except:
                return False
        else:
            return True

    @classmethod
    def get_images_names(cls):
        ''' 
            get image names in docker and update it 
        '''
        image_tags = set()
        image_names = set()

        images = cls.client.images.list()
        if images is not None:
            for image in images:
                if image is not None:
                    for tag in image.tags:
                        image_tags.add(tag)
        for image in image_tags:
            image_names.add(image.split(":")[0])
        cls.image_names = image_names

    @classmethod
    def check_image_name(cls, name: str) -> bool:
        '''
            check given image name is valid or not
        '''
        if name in cls.image_names:
            return True
        # try to flash image name
        cls.update_images_names()
        if name in cls.image_names:
            return True
        # image not in docker
        return False
