-----------------------------------
-- create test database and connect
-----------------------------------

DROP DATABASE IF EXISTS pymcachefdw_test;
CREATE DATABASE pymcachefdw_test;
ALTER DATABASE pymcachefdw_test OWNER TO postgres;

\connect pymcachefdw_test

SET client_min_messages TO DEBUG;

----------------------------
-- create helpful extensions
----------------------------

CREATE EXTENSION IF NOT EXISTS multicorn;

---------------------
-- create fdw servers
---------------------

DROP SERVER IF EXISTS pymcache_fdw CASCADE;

CREATE SERVER pymcache_fdw
FOREIGN DATA WRAPPER multicorn
OPTIONS (
    wrapper 'pymcache_fdw.PymcacheFDW'
);

DROP SERVER IF EXISTS pymcache_fdw_stat CASCADE;

CREATE SERVER pymcache_fdw_stat
FOREIGN DATA WRAPPER multicorn
OPTIONS (
    wrapper 'pymcache_fdw.PymcacheFDWStats'
);

------------------------
-- create foreign tables
------------------------

CREATE FOREIGN TABLE pymcache_test (
    key TEXT,
    value TEXT,
    expire TEXT
) SERVER pymcache_fdw OPTIONS (
    host 'localhost',
    port '11211',
    row_id 'key'
);

CREATE FOREIGN TABLE pymcache_stat_test (
    stat_name TEXT,
    stat_value TEXT
) SERVER pymcache_fdw_stat;

CREATE FOREIGN TABLE pymcache_stat_settings_test (
    stat_name TEXT,
    stat_value TEXT
) SERVER pymcache_fdw_stat OPTIONS (
    stats_cmd 'settings'
);

--------------
-- run queries
--------------

-- manipulate memcache items

INSERT INTO pymcache_test(key, value) VALUES('born_to_die', 'Lana Del Rey');

UPDATE pymcache_test SET value = 'Grand Funk Railroad' WHERE key = 'born_to_die';

SELECT * FROM pymcache_test WHERE key IN ('born_to_die', 'k1');
SELECT * FROM pymcache_test WHERE key = 'k2';

DELETE FROM pymcache_test WHERE key = 'born_to_die';

INSERT INTO pymcache_test(key, value, expire) VALUES('meaning_of_life', 42, 3600);

SELECT value FROM pymcache_test WHERE key = 'meaning_of_life';

DELETE FROM pymcache_test WHERE key IN ('meaning_of_life');

-- get statistics

SELECT * FROM pymcache_stat_test WHERE stat_name ~* 'connection';

SELECT * FROM pymcache_stat_settings_test WHERE stat_name ~* 'enabled';
