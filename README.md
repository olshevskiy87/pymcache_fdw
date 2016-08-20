pymcache\_fdw
=============

Memcache foreign data wrapper for PostgreSQL written in python.

dependencies
------------

- [pymemcache](https://pypi.python.org/pypi/pymemcache)
- [multicorn](http://multicorn.org/#idinstallation)

installation
------------

1. install python module

    ```bash
    $ cd /path/to/pymcache_fdw
    $ python setup.py install
    ```

2. create extension "multicorn"

    ```sql
    $$ create extension multicorn;
    ```

3. create foreign server in database

    ```sql
    $$ CREATE SERVER pymcache_fdw
    FOREIGN DATA WRAPPER multicorn
    OPTIONS (
        wrapper 'pymcache_fdw.PymcacheFDW'
    );
    ```

4. create foreign table

    ```sql
    $$ CREATE FOREIGN TABLE pymcache_test (
        key TEXT,
        value TEXT
    ) SERVER pymcache_fdw OPTIONS (
        host 'localhost',
        port '11211'
    );
    ```

usage
-----

- with set of keys in "where" clause

```sql
$$ select * from pymcache_test where key in ('k3', 'k1', 'k4');

 key |  value
-----+----------
 k3  | test 2
 k1  | test 1
 k4  | [1, 2]
(4 rows)
```

- with one exact cache key and one field "value" in results

```sql
$$ select value from pymcache_test where key = 'k3';

 value
--------
 test 2
(1 row)
```

external links
--------------

- [PostgreSQL foreign data wrappers](https://wiki.postgresql.org/wiki/Foreign_data_wrappers) (postgres wiki)
- [Multicorn](http://multicorn.org) - postgres extension that allows to make FDW with python language
- [Memcached](https://memcached.org) - distributed memory object caching system
- [Pymemcache](https://pymemcache.readthedocs.io/en/latest) python module documentation

license
-------

Copyright (c) 2016 Dmitriy Olshevskiy. MIT LICENSE.

See LICENSE.md for details.
