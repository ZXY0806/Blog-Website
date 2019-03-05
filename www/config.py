import config_default

configs = config_default.configs


class Dict(dict):
    def __init__(self, keys=(), values=(), **kwargs):
        super(Dict, self).__init__(**kwargs)
        for k, v in zip(keys, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r'has no attribute of "%s"' % str(key))

    def __setattr__(self, key, value):
        self[key] = value


def merge(default, override):
    r = {}
    for k, v in default.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r


def to_Dict(d):
    r = Dict()
    for k, v in d.items():
        r[k] = to_Dict(v) if isinstance(v, dict) else v
    return r


try:
    import config_override
    configs = merge(configs, config_override.configs)
except ImportError:
    pass
configs = to_Dict(configs)
