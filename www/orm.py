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


class Model(dict, metaclass=ModelMetaclass):

    def __init__(self, **kwargs):
        super(Model, self).__init__(**kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model'object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mapping__.get(key)
            if field is not None and field.default is not None:
                value = field.default() if callable(field.difault) else field.default
                logging.info('using default value for %s:%s' % (key, str(value)))
                setattr(self, key, value)
        return value


class ModelMetaclass(type):

    def __new__(cls, name, bases, attrs):

        #  排除Model类
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        tablename = attrs.get('__table__') or name
        logging.info('found model: %s (table: %s)' % (name, tablename))

        # 提取定义的field和主键名
        mappings = dict()
        fields = []
        primarykey = None
        for k, v in attrs.items:
            if isinstance(v, Field):
                mappings[k] = v
                if v.primary_key:
                    if primarykey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    primarykey = k
                else:
                    fields.append(k)
        if primarykey is None:
            raise RuntimeError('no primarykey in model')
        for k in mappings:
            attrs.pop(k)
        common_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__table__'] = tablename
        attrs['__mappings__'] = mappings
        attrs['__primary_key__'] = primarykey
        attrs['__fields__'] = fields
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primarykey, ', '.join(common_fields), tablename)
        attrs['__insert__'] = 'insert into `%s` (`%s`, %s) values (%s)' % (tablename, primarykey, ', '.join(common_fields), create_args_placeholder_str(len(fields)+1))
        



