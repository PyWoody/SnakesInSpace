import json
import logging
import os
import sqlite3

from datetime import datetime, timezone
from threading import Lock

# :memory: has rough edges
DATABASE = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'data', 'cache.db'
)
DATABSE_LOCK = Lock()
logger = logging.getLogger(__name__)


def get_waypoints(
        *,
        system,
        page_limit,
        page=0,
        traits=None,
        types=None,
        cache_mins=15,
):
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    params = {
        'system': system,
        'page_limit': int(page_limit),
        'page': int(page),
        'type': types if types is not None else '',
        'traits': traits if traits is not None else '',
    }
    keys = params.keys()  # I know it's ordered now but still
    where_string = ' AND '.join(f'{k} = (?)' for k in keys)
    query = cur.execute(f'''
        SELECT
            data, last_updated
        FROM
            waypoints
        WHERE
            {where_string}
        ''', tuple(params[k] for k in keys),
    )
    result = query.fetchone()
    con.close()
    if result:
        if last_updated := result[1]:  # pragma: no cover
            last_updated = datetime.fromisoformat(last_updated)
            delta = datetime.now(timezone.utc) - last_updated
            if delta.seconds and (delta.seconds / 60) >= cache_mins:
                return
        return json.loads(result[0])


def insert_waypoints(
    data,
    *,
    system,
    page_limit,
    page=0,
    types=None,
    traits=None,
):
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    params = {
        'system': system,
        'page_limit': int(page_limit),
        'page': int(page),
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'type': types if types is not None else '',
        'traits': traits if traits is not None else '',
    }
    keys = params.keys()  # I know it's ordered now but still
    insert_string = ', '.join(keys)
    values_string = ', '.join('?' for _ in range(len(keys)))
    update_values = [params[k] for k in keys]
    update_values.insert(0, json.dumps(data))

    # INSERT OR REPLACE/REPLACE INTO wasn't working reliably
    where_string = ' AND '.join(
        f'{k} = (?)' for k in keys if k != 'last_updated'
    )
    _ = cur.execute(f'''
        DELETE FROM
            waypoints
        WHERE
            ({where_string})
        ''', tuple(params[k] for k in keys if k != 'last_updated'))

    _ = cur.execute(f'''
        INSERT INTO
            waypoints (data, {insert_string})
        VALUES
            (json(?), {values_string})
        ''', update_values)
    result = False
    if cur.rowcount:
        con.commit()
        result = True
    else:  # pragma: no cover
        logger.warning(
            f'Failed to insert data for waypoints at page {page:,}'
        )
        con.rollback()
    con.close()
    return result


def setup():
    if not os.path.isfile(DATABASE):
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    _ = con.execute('''
        CREATE TABLE IF NOT EXISTS waypoints (
            pk INTEGER PRIMARY KEY ASC,
            system TEXT NOT NULL,
            page_limit INTEGER NOT NULL,
            page INTEGER NOT NULL,
            traits TEXT,
            type TEXT,
            last_updated TEXT,
            data TEXT NOT NULL
        );''')
    _ = con.commit()
    _ = cur.execute('PRAGMA journal_mode=WAL;')
    _ = con.commit()
    _ = cur.execute('DELETE FROM waypoints')
    _ = con.commit()
    con.close()
