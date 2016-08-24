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
        port '11211',
        row_id 'key'
    );
    ```

usage
-----

- set cache item

```sql
$$ insert into pymcache_test(key, value)
   values('meaning_of_life', '42');
INSERT 0 1
```

- get cache items with set of keys in "where" clause

```sql
$$ select key, value
   from pymcache_test
   where key in ('meaning_of_life', 'k1');

key              | value
-----------------+-------
meaning_of_life  | 42
(1 row)
```

- delete cache item with key `meaning_of_life`

```sql
$$ delete from pymcache_test
   where key = 'meaning_of_life';
DELETE 1
```

external links
--------------

- [PostgreSQL foreign data wrappers](https://wiki.postgresql.org/wiki/Foreign_data_wrappers) (postgres wiki)
- [Multicorn](http://multicorn.org) - postgres extension that allows to make FDW with python language
- [Memcached](https://memcached.org) - distributed memory object caching system
- [Pymemcache](https://pymemcache.readthedocs.io/en/latest) python module documentation

todo
----

 - [x] use "expire" parameter
 - [ ] use named parameters when calling pymemcache methods
 - [ ] add "update" query implementation
 - [ ] set proper PymcacheFDW -> pymemcache methods mapping

license
-------

Copyright (c) 2016 Dmitriy Olshevskiy. MIT LICENSE.

See LICENSE.md for details.
