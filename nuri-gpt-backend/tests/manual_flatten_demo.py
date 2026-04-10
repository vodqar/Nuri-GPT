def get_leaf_paths(data, current_path=""):
    paths = []
    if isinstance(data, dict):
        for k, v in data.items():
            new_path = f"{current_path}.{k}" if current_path else k
            if isinstance(v, (dict, list)):
                paths.extend(get_leaf_paths(v, new_path))
            else:
                paths.append(new_path)
    return paths

d = {"상단": {"일자": ""}, "자유놀이": {"실내": ""}}
print(get_leaf_paths(d))
