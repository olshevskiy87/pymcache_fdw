import json

from multicorn import ForeignDataWrapper
from multicorn.utils import log_to_postgres, DEBUG, WARNING, ERROR

from pymemcache.client.base import Client


class PymcacheFDW(ForeignDataWrapper):

    host = 'localhost'
    port = 11211

    _client = None

    columns = []
    _row_id_name = ''
    _expire = 0

    def __init__(self, options, columns):
        super(PymcacheFDW, self).__init__(options, columns)

        self.columns = columns

        # row_id column name
        if 'row_id' in options:
            self._row_id_name = options['row_id']
        else:
            self._row_id_name = list(self.columns.keys())[0]
            log_to_postgres(
                'Using first column as row_id name: %s' % self._row_id_name,
                WARNING)

        # "expire" value
        if 'expire' in options and options['expire'] is not None:
            self._expire = int(options['expire'])
        else:
            log_to_postgres(
                'Using default "expire" value: %s' % self._expire,
                WARNING)

        # memcache host name
        if 'host' in options:
            self.host = options['host']
        else:
            log_to_postgres('Using default host: %s' % self.host, WARNING)

        # memcache port
        if 'port' in options:
            self.port = int(options['port'])
        else:
            log_to_postgres('Using default port: %s' % self.port, WARNING)

        try:
            self._client = Client(
                (self.host, self.port),
                serializer=self.json_serializer,
                deserializer=self.json_deserializer
            )
        except Exception as e:
            log_to_postgres(
                'could not connect to memcache: %s' % str(e),
                ERROR)

    def json_serializer(self, key, value):
        if isinstance(value, str):
            return value, 1
        elif isinstance(value, unicode):
            return value, 0
        return json.dumps(value), 2

    def json_deserializer(self, key, value, flags):
        if flags in [0, 1]:
            return value
        if flags == 2:
            return json.loads(value)
        raise Exception('Unknown serialization format')

    # exec sql select-query
    def execute(self, quals, columns):
        log_to_postgres('exec quals: %s' % quals, DEBUG)
        log_to_postgres('exec columns: %s' % columns, DEBUG)

        key_column_exist = 'key' in columns

        # define cache keys
        cache_keys = []
        for q in quals:
            if (q.field_name != 'key' or
               not (
                   isinstance(q.operator, unicode) and q.operator == u'=' or
                   isinstance(q.operator, tuple) and q.operator[0] == u'='
               )):
                continue

            if isinstance(q.value, (str, unicode)):
                cache_keys = [q.value]
            elif isinstance(q.value, list):
                cache_keys = q.value
            break

        if not cache_keys:
            log_to_postgres('cache keys are not specified', DEBUG)
            return

        res_rows = self._client.get_multi(keys=cache_keys)

        for row in res_rows.iteritems():
            ret = {'value': row[1]}
            if key_column_exist:
                ret['key'] = row[0]
            yield ret

    @property
    def rowid_column(self):
        log_to_postgres('rowid requested', DEBUG)
        return self._row_id_name

    # exec insert-query
    def insert(self, item):
        log_to_postgres('insert value: %s' % item, DEBUG)

        if 'key' not in item or 'value' not in item:
            log_to_postgres('"key" and "value" must be specified', ERROR)

        expire_cur = self._expire
        if 'expire' in item and item['expire'] is not None:
            expire_cur = int(item['expire'])

        try:
            self._client.set(item['key'], item['value'], expire=expire_cur)
        except Exception as e:
            log_to_postgres(
                'could not set cache item %s: %s' % (item, str(e)),
                ERROR)

    # exec delete-query
    def delete(self, key):
        log_to_postgres('delete cache with key: %s' % key, DEBUG)
        try:
            self._client.delete(key)
        except Exception as e:
            log_to_postgres(
                'could not delete cache item with key "%s": %s' % (key, str(e)),
                ERROR)
