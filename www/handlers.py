import re, time, json, hashlib, base64, logging
from aiohttp import web
from coroweb import get, post
from models import User, Comment, Blog, next_id
from apis import Page, APIPermissionError, APIResourceNotFoundError, APIValueError, APIError
from config import configs
'''
获取日志：GET /api/blogs
创建日志：POST /api/blogs
修改日志：POST /api/blogs/:blog_id
删除日志：POST /api/blogs/:blog_id/delete
获取评论：GET /api/comments
创建评论：POST /api/blogs/:blog_id/comments
删除评论：POST /api/comments/:comment_id/delete
创建新用户：POST /api/users
获取用户：GET /api/users
评论列表页：GET /manage/comments
日志列表页：GET /manage/blogs
创建日志页：GET /manage/blogs/create
修改日志页：GET /manage/blogs/
用户列表页：GET /manage/users
注册页：GET /register
登录页：GET /signin
注销页：GET /signout
首页：GET /
日志详情页：GET /blog/:blog_id
'''

COOKIE_NAME = 'blog-website'
_COOKIE_KEY = configs.session.secret


def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()


def get_page_index(page_str):
    p = 1
    try:
        page_index = int(page_str)
        if page_index > 1:
            p = page_index
    except ValueError as e:
        pass
    return p


def user2cookie(user, max_age):
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    sha1 = hashlib.sha1(s.encode('utf-8')).hexdigest()
    L = [user.id, expires, sha1]
    return '-'.join(L)


async def cookie2user(cookie_str):
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if expires < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid cookie_str')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None


def text2html(text):
    lines = filter(lambda s: s.strip() != '', text.split('\n'))
    html_lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&alt;').replace('<', '&lt;').replace('>', '&gt'), lines)
    return ''.join(html_lines)


@get('/')
async def index(page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        blogs = []
    else:
        blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return {
        '__template__': 'index.html',
        'page': p,
        'blogs': blogs
    }


