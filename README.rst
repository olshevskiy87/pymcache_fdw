|pypi_badge|

############
pymcache_fdw
############

Memcache foreign data wrapper for PostgreSQL written in python.

************
dependencies
************

* `pymemcache <https://pypi.python.org/pypi/pymemcache>`__
* `multicorn <http://multicorn.org/#idinstallation>`__

************
installation
************

1. install python module

 * from sources (bitbucket)

    ::

        $ git clone https://bitbucket.org/olshevskiy87/pymcache_fdw.git
        $ cd pymcache_fdw
        $ python setup.py install

 * using pip

    ::

        $ pip install pymcache_fdw

2. create extension "multicorn"

    ::

        $$ create extension multicorn;

3. create foreign server in database

 * foreign server to operate cache items

    ::

        $$ CREATE SERVER pymcache_fdw
        FOREIGN DATA WRAPPER multicorn
        OPTIONS (
            wrapper 'pymcache_fdw.PymcacheFDW'
        );

 * foreign server to show statistics

    ::

        $$ CREATE SERVER pymcache_fdw_stat
        FOREIGN DATA WRAPPER multicorn
        OPTIONS (
            wrapper 'pymcache_fdw.PymcacheFDWStats'
        );

4. create foreign table

 * foreign table to operate cache items

    ::

        $$ CREATE FOREIGN TABLE pymcache_test (
            key TEXT,
            value TEXT,
            expire TEXT -- optional
        ) SERVER pymcache_fdw OPTIONS (
            host 'localhost',
            port '11211',
            row_id 'key',
            expire '60' -- optional, default is 0 - never expire
        );

 * foreign table to operate cache items with prefix in the keys

    ::

        $$ CREATE FOREIGN TABLE pymcache_test_group (
            key TEXT,
            value TEXT
        ) SERVER pymcache_fdw OPTIONS (
            prefix 'group1_'
        );

 * foreign table to show general-purpose statistics

    ::

        $$ CREATE FOREIGN TABLE pymcache_stat_test (
            stat_name TEXT,
            stat_value TEXT
        ) SERVER pymcache_fdw_stat;

 * foreign table to show current memcache settings

    ::

        $$ CREATE FOREIGN TABLE pymcache_stat_settings_test (
            stat_name TEXT,
            stat_value TEXT
        ) SERVER pymcache_fdw_stat OPTIONS (
            stats_cmd 'settings'
        );

*****
usage
*****

* set cache item

::

    $$ insert into pymcache_test(key, value)
       values('meaning_of_life', '42');
    INSERT 0 1

* set cache item, that will expire after 10 seconds

::

    $$ insert into pymcache_test(key, value, expire)
       values('born_to_die', 'Lana Del Rey', 10);
    INSERT 0 1

* update cache item with key `born_to_die`

::

    $$ update pymcache_test
       set value = 'Grand Funk Railroad', expire = 300
       where key = 'born_to_die'
    UPDATE 1

* get cache items with set of keys in "where" clause

::

    $$ select key, value
       from pymcache_test
       where key in ('meaning_of_life', 'k1');

           key       | value
    -----------------+-------
    meaning_of_life  | 42
    (1 row)

* delete cache item with key `meaning_of_life`

::

    $$ delete from pymcache_test
       where key = 'meaning_of_life';
    DELETE 1

* set and get items with key prefix `group1_`

::

    $$ insert into pymcache_test_group(key, value)
       values('first_item', 'first value');
    INSERT 0 1

    $$ select key, value
       from pymcache_test_group
       where key = 'first_item';

        key     |    value
    ------------+-------------
     first_item | first value
    (1 row)

* show general-purpose statistics related to connections

::

    $$ select stat_name, stat_value
       from pymcache_stat_test
       where stat_name ~* 'connection';

    WARNING:  Using default host: localhost
    WARNING:  Using default port: 11211
           stat_name       | stat_value
    -----------------------+------------
     curr_connections      | 6
     total_connections     | 31
     connection_structures | 7
    (3 rows)

* show "enabled" memcache settings

::

    $$ select stat_name, stat_value
       from pymcache_stat_settings_test
       where stat_name ~* 'enabled';

         stat_name     | stat_value
    -------------------+------------
     cas_enabled       | yes
     auth_enabled_sasl | False
     detail_enabled    | no
     flush_enabled     | yes
    (4 rows)

**************
external links
**************

* `PostgreSQL foreign data wrappers <https://wiki.postgresql.org/wiki/Foreign_data_wrappers>`__
* `Multicorn <http://multicorn.org>`__ - postgres extension that allows to make FDW with python language
* `Memcached <https://memcached.org>`__ - distributed memory object caching system
* `memcached protocol <https://github.com/memcached/memcached/blob/master/doc/protocol.txt>`__
* `Pymemcache <https://pymemcache.readthedocs.io/en/latest>`__ - python module documentation

*******
license
*******

Copyright (c) 2016 Dmitriy Olshevskiy. MIT LICENSE.

See LICENSE.txt for details.

.. |pypi_badge| image:: https://badge.fury.io/py/pymcache_fdw.svg
    :target: https://pypi.python.org/pypi/pymcache-fdw
