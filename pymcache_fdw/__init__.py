import json
from collections import OrderedDict

from multicorn import ForeignDataWrapper
from multicorn.utils import log_to_postgres, DEBUG, WARNING, ERROR

from pymemcache.client.base import Client


class PymcacheFDW(ForeignDataWrapper):

    host = 'localhost'
    port = 11211

    _client = None

    columns = []
    _row_id_name = ''

    def __init__(self, options, columns):
        super(PymcacheFDW, self).__init__(options, columns)

        self.columns = columns

        if 'row_id' in options:
            self._row_id_name = options['row_id']
        else:
            self._row_id_name = list(self.columns.keys())[0]
            log_to_postgres(
                'Using first column as row_id name: %s' % self._row_id_name,
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

        # define cache key
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
            row_ord = OrderedDict()
            if 'key' in columns:
                row_ord['key'] = row[0]

            row_ord['value'] = row[1]
            yield row_ord

    @property
    def rowid_column(self):
        log_to_postgres('rowid requested', DEBUG)
        return self._row_id_name

    # exec insert-query
    def insert(self, val):
        log_to_postgres('insert value: %s' % val, DEBUG)

        if 'key' not in val or 'value' not in val:
            log_to_postgres('"key" and "value" must be specified', ERROR)

        try:
            self._client.set(val['key'], val['value'])
        except Exception as e:
            log_to_postgres(
                'could not set cache item %s: %s' % (val, str(e)),
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
