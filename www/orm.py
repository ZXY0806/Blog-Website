import aiomysql, asyncio, logging


def log(sql, args=()):
    logging.info('SQL:%s,args:%s' % (sql, args))


async def create_pool(loop, **kwargs):
    log('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        loop=loop,
        host=kwargs.get('host', 'localhost'),
        port=kwargs.get('port', 3306),
        user=kwargs['user'],
        password=kwargs['password'],
        db=kwargs['db'],
        autocommit=kwargs.get('autocommit', True),
        charset=kwargs.get('charset', 'utf-8'),
        maxsize=kwargs.get('maxsize', 10),
        minsize=kwargs.get('minsize', 1)
    )


async def select(sql, args, size=None):
    log(sql, args)
    global __pool
    with (await __pool) as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = await cur.fetchmany(size)
        else:
            rs = await cur.fetchall()
        await cur.close()
        logging.info('rows returned:%s' % len(rs))
        return rs


async def execute(sql, args):
    log(sql, args)
    global __pool
    with (await __pool) as conn:
        try:
            cur = await conn.cursor()
            await cur.execute(sql.replace('?', '%s'), args or ())
            affected = cur.rowcount
            await cur.close()
        except BaseException as e:
            raise
        return affected


class Field(object):

    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class StringField(Field):

    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name=name, column_type=ddl, primary_key=primary_key, default=default)


class BooleanField(Field):

    def __init__(self, name=None, default=False):
        super(BooleanField, self).__init__((name, 'boolean', False, default))


class IntField(Field):

    def __init__(self, name=None, primary_key=False, default=0):
        super(IntField, self).__init__((name, 'bigint', primary_key, default))


class FloatField(Field):

    def __init__(self, name=None, primary_key=False, default=0.0):
        super(FloatField, self).__init__((name, 'real', primary_key, default))


class TextField(Field):

    def __init__(self, name=None, default=None):
        super().__init__(name=name, column_type='text', primary_key=False, default=default)


