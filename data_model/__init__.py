from .service import Function, Service
from .schema import FunctionSchema, ServiceSchema, ServiceRuntimeSchema

# service schema and function schema
# for service definition
schemaFunc = FunctionSchema()
schemaServ = ServiceSchema()

# service runtime schema and function runtime schema
# for user request
schemaServRuntime = ServiceRuntimeSchema()
