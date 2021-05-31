import base64
import json
from typing import Dict

test = '{}'

print(isinstance(json.loads(test), dict))


print(base64.decodebytes(b"YWRtaW46RjNKbndOMEhwY05G"))
print(base64.encodebytes(b"admin:F3JnwN0HpcNF\n"))
