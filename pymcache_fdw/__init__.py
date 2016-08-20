import json
from collections import OrderedDict

from multicorn import ForeignDataWrapper
from multicorn.utils import log_to_postgres, DEBUG, WARNING, ERROR

from pymemcache.client.base import Client


class PymcacheFDW(ForeignDataWrapper):

    host = 'localhost'
    port = 11211

    columns = []

    def __init__(self, options, columns):
        super(PymcacheFDW, self).__init__(options, columns)

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

        self.columns = columns

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

    # exec sql query
    def execute(self, quals, columns):

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

        # cache "value", check column name
        if 'value' not in columns:
            log_to_postgres('there must be a "value" column', ERROR)

        client = Client(
            (self.host, self.port),
            serializer=self.json_serializer,
            deserializer=self.json_deserializer
        )
        res_rows = client.get_multi(keys=cache_keys)

        for row in res_rows.iteritems():
            row_ord = OrderedDict()
            if 'key' in columns:
                row_ord['key'] = row[0]

            row_ord['value'] = row[1]
            yield row_ord

        client.close()

    def insert(self, new_values):
        log_to_postgres('insert, new values: %s' % new_values, DEBUG)

    def update(self, rowid, new_values):
        log_to_postgres('update, rowid: %s' % new_values, DEBUG)
        log_to_postgres('update, new values: %s' % new_values, DEBUG)

    def delete(self, rowid):
        log_to_postgres('delete, rowid: %s' % rowid, DEBUG)
