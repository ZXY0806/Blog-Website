import asyncio, os, inspect, logging, functools
from aiohttp import web
from urllib import parse


def get(path):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator


def post(path):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__router__ = path
        return wrapper
    return decorator


def get_required_kwargs(func):
    args = []
    params = inspect.signature(func).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)


def has_var_kwargs(func):
    params = inspect.signature(func).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True


def has_named_kwargs(func):
    params = inspect.signature(func).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True


def get_named_kwargs(func):
    args = []
    params = inspect.signature(func).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)


def has_request_kwargs(func):
    sig = inspect.signature(func)
    params = sig.parameters  # 返回值为有序字典
    found = False
    for name, param in params.items():
        if name == 'request':
            found = True
            continue
        if found == True and param.kind != inspect.Parameter.VAR_KEYWORD:
            return ValueError('request parameter must be the last named parameter in function: %s%s' % (func.__name__,
                                                                                                        str(sig)))
    return found


