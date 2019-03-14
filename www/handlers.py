import re, time, json, hashlib, base64, logging, markdown
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
修改日志页：GET /manage/blogs/edit
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


@get('/register')
def register():
    return {
        '__template__': 'register.html'
    }


@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
    }


@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly='True')
    logging.info('user signout')
    return r


@post('/api/authenticate')
async def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'invalid email')
    if not passwd:
        raise APIValueError('passwd', 'invalid passwd')
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'email not exist')
    user = users[0]
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'invalid passwd')
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), expires='86400', httponly='True')
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@get('/manage/users')
def manage_users(*, page='1'):
    return {
        '__template__': 'manage_users.html',
        'page_index': get_page_index(page)
    }


@get('/manage/comments')
def manage_comments(*, page='1'):
    return {
        '__template__': 'manage_comments.html',
        'page_index': get_page_index(page)
    }


@get('/manage/blogs')
def manage_blogs(*, page='1'):
    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page)
    }


@get('/manage/blogs/create')
def manage_create_blog():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'
    }


@get('/manage/blogs/edit')
def manage_blog_edit(*, blog_id):
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id,
        'action': '/api/blogs/%s' % blog_id
    }


@get('/api/users')
async def api_users(*, page='1'):
    num = await User.findNumber('count(id)')
    p = Page(num, get_page_index(page))
    if num == 0:
        return dict(page=p, users=())
    users = await User.findAll(orderBy='created_at desc', limit=(p.offset,p.limit))
    for u in users:
        u.passwd = '******'
    return dict(page=p, users=users)


_RE_EMAIL = re.compile(r'^[a-zA-Z0-9.-_]+@[0-9a-z-_]+(.[a-z0-9-_]){1-4}$')
_RE_SHA = re.compile(r'^[a-z0-9]{40}$')


@post('/api/users')
async def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA.match(passwd):
        raise APIValueError('passwd')
    users = await User.findAll('email=?', [email])
    if len(users) != 0:
        raise APIError('register:failed', 'email', 'email has already in use')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = User(id=uid, email=email, name=name, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest())
    await user.save()
    r = web.Response()
    r.content_type = 'application/json'
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly='True')
    user.passwd = '******'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@get('/api/comments')
async def api_comments(*, page='1'):
    num = await Comment.findNumber('count(id)')
    page_index = get_page_index(page)
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, comments=())
    comments = await Comment.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)


@post('/api/comments/{comment_id}/delete')
async def api_delete_comment(comment_id, request):
    check_admin(request)
    comment = await Comment.find(comment_id)
    if comment is None:
        return APIResourceNotFoundError('comment')
    await comment.remove()
    return dict(id=comment_id)


@post('/api/blogs/{blog_id}/comments')
async def api_create_comment(blog_id, request, *, content):
    user = request.__user__
    if user is None:
        raise APIPermissionError('please signin first')
    if not content or not content.strip():
        raise APIValueError('content')
    blog = await Blog.find(blog_id)
    if blog is None:
        raise APIValueError('blog_id')
    comment = Comment(user_name=user.name, user_id=user.id, user_image=user.image, blog_id=blog_id, content=content.strip())
    await comment.save()
    return comment


@get('/blog/{blog_id}')
async def get_blog(blog_id):
    blog = await Blog.find(blog_id)
    comments = await Comment.findAll('blog_id=?', [blog_id], orderBy='created_at desc')
    for c in comments:
        c.html_content = markdown.markdown(c.content)
    blog.html_content = markdown.markdown(blog.content)
    return {
        '__template__': 'blog.html',
        'comments': comments,
        'blog': blog
    }


@get('/api/blogs')
async def api_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)


@post('/api/blogs/{blog_id}/delete')
async def api_delete_blogs(blog_id, request):
    user = request.__user__
    check_admin(user)
    blog = await Blog.find(blog_id)
    if blog is None:
        raise APIResourceNotFoundError('blog')
    await blog.remove()
    return dict(id=blog_id)


@post('/api/blogs/{blog_id}')
async def api_update_blog(blog_id, request, *, name, summary, content):
    user = request.__user__
    check_admin(user)
    blog = await Blog.find(blog_id)
    if blog is None:
        raise APIResourceNotFoundError('blog', 'invalid blog id')
    if not name or not name.strip():
        raise APIValueError('name', 'name can not be empty')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary can not be empty')
    if not content or not content.strip():
        raise APIValueError('content', 'content can not be empty')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    await blog.update()
    return blog


@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    user = request.__user__
    check_admin(user)
    if not name or not name.strip():
        raise APIValueError('name', 'name can not be empty')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary can not be empty')
    if not content or not content.strip():
        raise APIValueError('content', 'content can not be empty')
    blog = Blog(user_name=user.name, user_id=user.id, user_image=user.image, name=name.strip(), summary=summary.strip(),
                content=content.strip())
    await blog.save()
    return blog


@post('/api/users/{user_id}/delete')
async def api_delete_user(user_id, request):
    buff_id = user_id
    user = request.__user__
    check_admin(user)
    user = await User.find(user_id)
    if user is None:
        raise APIResourceNotFoundError('user', 'user is not exist')
    await user.remove()
    comments = await Comment.findAll('user_id=?', [buff_id])
    for c in comments:
        c.user_name = c.user_name + '(该用户已被删除)'
        await c.update()
    return dict(id=buff_id)






