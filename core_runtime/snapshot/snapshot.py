import zlib
from core_runtime.runtime_container.runtime import Runtime, RuntimeError
from data_model import schemaServRuntime
from typing import Optional, Tuple
from data_model.service_runtime import ServiceRuntime, ServiceState


class SnapshotController:
    @classmethod
    def take_snapshot(cls, user_token: str, service_token: str) -> Tuple[Optional[bytes],
                                                                         Optional[RuntimeError]]:
        service_runtime, err = Runtime.snapshot(user_token,
                                                service_token)
        if err != None:
            return None, err

        runtime_str, err = cls.marshal(service_runtime)
        if err != None:
            return None, err

        runtime_compress, err = cls.compress_snapshot(runtime_str)
        return runtime_compress, err

    @classmethod
    def run_snapshot(cls, user_token: str, service_runtime_bytes: bytes) -> Tuple[Optional[str],
                                                                                  Optional[RuntimeError]]:

        service_runtime_str, err = cls.decompress_snapshot(
            service_runtime_bytes)
        if err != None:
            return None, err

        service_runtime, err = cls.demarshal(service_runtime_str)
        if err != None:
            return None, err

        # it's fine
        service_token, err = Runtime.restore_snapshot(
            user_token, service_runtime)

        return service_token, err

    @classmethod
    def marshal(cls, service_runtime: ServiceRuntime) -> Tuple[Optional[str],
                                                               Optional[RuntimeError]]:
        try:
            runtime_str: str = schemaServRuntime.dumps(service_runtime)
            return runtime_str, None
        except Exception as e:
            return None, RuntimeError("marshal failed: %s" % str(e))

    @classmethod
    def demarshal(cls, service_runtime_str: Optional[str]) -> Tuple[Optional[ServiceRuntime],
                                                                    Optional[RuntimeError]]:
        try:
            # it's fine
            runtime = schemaServRuntime.loads(service_runtime_str)
            return runtime, None
        except Exception as e:
            return None, RuntimeError("can't parse runtime from file, please check file: %s"
                                      % str(e))

    @classmethod
    def compress_snapshot(cls, service_runtime_str: str) -> Tuple[Optional[bytes],
                                                                  Optional[RuntimeError]]:
        try:
            return zlib.compress(
                service_runtime_str.encode("utf-8")), None
        except Exception as e:
            return None, RuntimeError("compress failed: %s" % str(e))

    @classmethod
    def decompress_snapshot(cls,
                            service_runtime_bytes: bytes) -> Tuple[Optional[str],
                                                                   Optional[RuntimeError]]:
        try:
            return zlib.decompress(service_runtime_bytes).decode("utf-8"), None
        except Exception as e:
            return None, RuntimeError("decompress failed: %s" % str(e))
