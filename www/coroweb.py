import asyncio, os, inspect, logging, functools
from aiohttp import web
from urllib import parse
from apis import APIError


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
        wrapper.__route__ = path
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
        self._named_kwargs = get_named_kwargs(func)
        self._has_var_kwargs = has_var_kwargs(func)
        self._has_named_kwargs = has_named_kwargs(func)
        self._has_request_arg = has_request_arg(func)

    async def __call__(self, request):
        kw = None
        if self._has_var_kwargs or self._has_named_kwargs or self._required_kwargs:
            if request.method == 'POST':
                if not request.content_type:
                    return web.HTTPBadRequest('Missing content_type')
                ct = request.content_type.lower()
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('json body must be object')
                    kw = params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipate/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('unexpected content-type:%s' % ct)
            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]
        if kw is None:
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kwargs and self._named_kwargs:
                copy = dict()
                for k in self._named_kwargs:
                    if k in kw:
                        copy[k] = kw[k]
                kw = copy
            for k, v in request.match_info.items():
                if k in kw:
                    logging.warning('duplicate arg name in named args and key args:%s' % k)
                kw[k] = v
        if self._has_request_arg:
            kw['request'] = request
        for name in self._required_kwargs:
            if name not in kw:
                return web.HTTPBadRequest('Missing argument:{}'.format(name))
        logging.info('call with func:%s;args:%s' % (str(self._func), str(kw)))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)


def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))


def add_route(app, func):
    method = getattr(func, '__method__', None)
    path = getattr(func, '__route__', None)
    if method is None or path is None:
        raise ValueError('@get or @post not defined in func:%s.' % func.__name__)
    if not asyncio.iscoroutine(func) and not inspect.isgeneratorfunction(func):
        func = asyncio.coroutine(func)
    logging.info('add route %s %s : %s(%s)' % (method, path, func.__name__,
                                               ', '.join(inspect.signature(func).parameters.keys())))
    app.router.add_route(method, path, RequestHandler(app, func))


def add_routes(app, model_name):
    n = model_name.rfind('.')
    if n == -1:
        mod = __import__(model_name, globals(), locals())
    else:
        name = model_name[n+1:]
        mod = getattr(__import__(model_name[:n], globals(), locals(), [name]), name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        func = getattr(mod, attr)
        method = getattr(func, '__method__', None)
        route = getattr(func, '__route__', None)
        if method and route:
            add_route(app, func)








