import toposort
function_dict = {
    1: {2, 3},
    2: {3},
    3: {4}
}
print(list(toposort.toposort_flatten(function_dict, sort=True)))

function_dict2 = {
    1: [2, 3],
    2: [3],
    3: [4]
}

function_dict3 = {}
for k, v in function_dict2.items():
    function_dict3[k] = set(v)

print(list(toposort.toposort_flatten(function_dict3, sort=True)))
