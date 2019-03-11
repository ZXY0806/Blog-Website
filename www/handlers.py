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


