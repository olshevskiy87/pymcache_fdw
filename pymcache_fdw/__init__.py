from multicorn import ForeignDataWrapper
from multicorn.utils import log_to_postgres, DEBUG, WARNING, ERROR

from pymemcache.client.base import MemcacheUnknownCommandError

import utils


class PymcacheFDW(ForeignDataWrapper):

    _row_id_name = ''
    _expire = 0

    def __init__(self, options, columns):
        super(PymcacheFDW, self).__init__(options, columns)

        # row_id column name
        if 'row_id' in options:
            self._row_id_name = options['row_id']
        else:
            self._row_id_name = columns.keys()[0]
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

        # "prefix" value
        self._prefix = options.get('prefix', '')
        if self._prefix is None:
            self._prefix = ''
        self._prefix_size = len(self._prefix)
        log_to_postgres('Using "prefix" value: %s' % self._prefix, WARNING)

        self._client = utils.connect(options)

    def _get_expire(self, item=None):
        ret = self._expire
        if item is not None:
            try:
                ret = int(item['expire'])
            except:
                pass
        return ret

    def _make_full_key(self, key):
        if not self._prefix:
            return key

        if isinstance(key, basestring):
            key = '%s%s' % (self._prefix, key)
        elif isinstance(key, list):
            key = ['%s%s' % (self._prefix, k) for k in key]
        else:
            key = ''
        return key

    # exec sql select-query
    def execute(self, quals, columns):
        log_to_postgres('exec quals: %s' % quals, DEBUG)
        log_to_postgres('exec columns: %s' % columns, DEBUG)

        key_column_exist = self._row_id_name in columns

        # define cache keys
        cache_keys = []
        for q in quals:
            if (q.field_name != self._row_id_name or
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

        res_rows = self._client.get_multi(keys=self._make_full_key(cache_keys))

        for row in res_rows.iteritems():
            ret = {'value': row[1]}
            if key_column_exist:
                ret[self._row_id_name] = row[0][self._prefix_size:]
            yield ret

    @property
    def rowid_column(self):
        log_to_postgres('rowid requested', DEBUG)
        return self._row_id_name

    # exec insert-query
    def insert(self, item):
        log_to_postgres('insert value: %s' % item, DEBUG)

        if self._row_id_name not in item or 'value' not in item:
            log_to_postgres(
                '"%s" and "value" must be specified' % self._row_id_name,
                ERROR)

        key = self._make_full_key(item[self._row_id_name])
        try:
            res = self._client.add(
                key,
                item['value'],
                expire=self._get_expire(item),
                noreply=False)
            if not res:
                raise Exception('key "%s" is already exist' % key)
        except Exception as e:
            log_to_postgres(
                'could not add cache item: %s' % str(e),
                ERROR)

    # exec update-query
    def update(self, key, item):
        log_to_postgres('key: %s' % key, DEBUG)
        log_to_postgres('new values: %s' % item, DEBUG)

        if 'value' not in item:
            log_to_postgres('"value" must be specified', ERROR)

        try:
            self._client.set(
                self._make_full_key(key),
                item['value'],
                expire=self._get_expire(item))
        except Exception as e:
            log_to_postgres(
                'could not set cache item %s: %s' % (item, str(e)),
                ERROR)

    # exec delete-query
    def delete(self, key):
        log_to_postgres('delete cache with key: %s' % key, DEBUG)
        try:
            self._client.delete(self._make_full_key(key))
        except Exception as e:
            log_to_postgres(
                'could not delete cache item with key "%s": %s' % (key, str(e)),
                ERROR)


class PymcacheFDWStats(ForeignDataWrapper):

    allowed_stats_cmds = ['items', 'settings', 'slabs', 'sizes', 'conns']

    # current stats command
    # by default show general-purpose statistics (empty stats command)
    _stats_cmd = ''

    def __init__(self, options, columns):
        super(PymcacheFDWStats, self).__init__(options, columns)

        if 'stats_cmd' in options:
            if options['stats_cmd'] in self.allowed_stats_cmds:
                self._stats_cmd = options['stats_cmd']
            else:
                log_to_postgres(
                    'stats command "%s" is not allowed' % options['stats_cmd'],
                    ERROR)

        self._client = utils.connect(options)

    # exec sql select-query
    def execute(self, quals, columns):
        stats = {}
        try:
            stats = self._client.stats(self._stats_cmd)
        except MemcacheUnknownCommandError as e:
            log_to_postgres(
                'unknown memcache command "%s": %s' % (self._stats_cmd, str(e)),
                ERROR)
        except Exception as e:
            log_to_postgres(
                'could not get statistics: %s' % str(e),
                ERROR)

        for stat in stats.iteritems():
            yield stat
