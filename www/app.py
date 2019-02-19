import logging; logging.basicConfig(level=logging.INFO)
import asyncio, os, time, json, sys
from aiohttp import web
from .models import User, Blog, Comment
from .orm import create_pool


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

