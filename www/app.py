import logging; logging.basicConfig(level=logging.INFO)
import asyncio, os, time, json, sys
from aiohttp import web
from models import User, Blog, Comment
from orm import create_pool
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from coroweb import add_static, add_routes


def index(request):
    return web.Response(body=b'<h1>welcome</h1>', content_type='text/html')


async def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    return app


def main():
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init(loop))
    web.run_app(app, host='172.16.3.111', port=9000)
    logging.info('server started at http://127.0.0.1:9000 ...')


def init_jinja2(app, **kw):
    logging.info('init jinja2 ...')
    options = dict(
        autoescape=kw.get('autoescape', True),
        block_start_string=kw.get('block_start_string', '{%'),
        block_end_string=kw.get('block_end_string', '%}'),
        variable_start_string=kw.get('variable_start_string', '{{'),
        variable_end_string=kw.get('variable_end_string', '}}'),
        auto_reload=kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 templates path:%s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for k, v in filters.items():
            env.filters[k] = v
    app['__templating__'] = env


async def logger_factory(app, handler):
    async def logger(request):
        logging.info('request:%s %s' % (request.method, request.path))
        return await handler(request)
    return logger


async def data_factory(app, handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                logging.info('request json:%s' % request.__data__)
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request form:%s' % request.__data__)
        return await handler(request)
    return parse_data


async def response_factory(app, handler):
    async def response(request):
        logging.info('handle request ...')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and 100 <= r < 600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            v, t = r
            if isinstance(v, int) and 100 <= v < 600:
                return web.Response(v, str(r))
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response


def time_filter(t):
    t_pass = int(time.time() - t)
    if t_pass < 60:
        return u'1分钟前'
    if t_pass < 3600:
        return u'%s分钟前' % (t_pass // 60)
    if t_pass < 86400:
        return u'%s小时前' % (t_pass // 3600)
    if t_pass < 604800:
        return u'%s天前' % (t_pass // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


async def test(loop):
    await create_pool(loop=loop, user='root', password='sa', db='blog_website')
    u = User(id='1', name='小明', email='email', image='image', passwd='passwd')
    await u.save()


if __name__ == '__main__':
    print('test')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(loop))
    loop.close()
    sys.exit(0)  # loop直接close会抛出RunError异常，具体机制还要看文档，理解loop运行机制

