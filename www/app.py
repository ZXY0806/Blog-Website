import logging; logging.basicConfig(level=logging.INFO)
import asyncio, os, time, json
from aiohttp import web


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


if __name__ == '__main__':
    main()

