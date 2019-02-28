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


def has_request_arg(func):
    sig = inspect.signature(func)
    params = sig.parameters  # 返回值为有序字典
    found = False
    for name, param in params.items():
        if name == 'request':
            found = True
            continue
        if found and param.kind != inspect.Parameter.VAR_KEYWORD:
            return ValueError('request parameter must be the last named parameter in function: %s%s' % (func.__name__,
                                                                                                        str(sig)))
    return found


class RequestHandler(object):

    def __init__(self, app, func):
        self._app = app
        self._func = func
        self._required_kwargs = get_required_kwargs(func)
        self._has_var_kwargs = has_var_kwargs(func)
        self._has_named_kwargs = has_named_kwargs(func)
        self._has_request_arg = has_request_arg(func)

    async def __call__(self, request):
        kw = None
        if self._has_var_kwargs or self._has_named_kwargs or self._required_kwargs:
            if request.method == 'POST':
                pass
            if request.method == 'GET':
                pass
        if kw is None:
            kw = dict(**request.match_info)
        else:
            pass
        if self._has_request_arg:
            kw['request'] = request
        for name in self._required_kwargs:
            if name not in kw:
                return web.HTTPBadRequest('Missing argument:{}'.format(name))
        logging.info('call with args:%s' % str(kw))
        try:
            r = await self._func(**kw)
            return r
        except:
            # APIError
            pass





