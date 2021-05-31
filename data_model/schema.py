from marshmallow import Schema, fields, post_load
from data_model.service import Service, Function
from data_model.service_runtime import ServiceRuntime, ServiceState, DataContainer


class FunctionSchema(Schema):
    '''
        function data schema using marshmallow
        use it to marshal/un-marshal function to json
    '''
    name = fields.Str()
    function_id = fields.Int()

    @post_load
    def make(self, data, **kwargs):
        return Function(**data)


class ServiceSchema(Schema):
    '''
        service data schema using marshmallow
        use it to marshal/un-marshal service to json
    '''
    name = fields.Str()
    first_function = fields.Int()
    function_dict = fields.Dict(
        keys=fields.Int(),
        values=fields.List(fields.Int()))
    # values=fields.Nested(FunctionSchema())

    function_list = fields.List(fields.Nested(FunctionSchema))
    is_realtime = fields.Bool()

    @post_load
    def make(self, data, **kwargs):
        return Service(**data)


class DataContainerSchema(Schema):

    data = fields.Raw()
    ref_cnt = fields.Int()

    @post_load
    def make(self, data, **kwargs):
        return DataContainer(**data)


class ServiceStateSchema(Schema):
    service_queue = fields.List(fields.Int())
    service_data = fields.Dict(
        keys=fields.Int(),
        values=fields.Nested(DataContainerSchema)
    )
    service_input_data = fields.String()
    service_output_data = fields.String()

    @post_load
    def make(self, data, **kwargs):
        return ServiceState(**data)


class ServiceRuntimeSchema(Schema):
    service = fields.Nested(ServiceSchema())
    service_state = fields.Nested(ServiceStateSchema())

    @post_load
    def make(self, data, **kwargs) -> ServiceRuntime:
        return ServiceRuntime(**data)
