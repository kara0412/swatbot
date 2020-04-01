import time
from collections import defaultdict

import psycopg2

from settings import env_vars

in_memory_swat_count_dict = defaultdict(int)


def get_conn():
    return psycopg2.connect(env_vars["DATABASE_URL"], sslmode='require')

def update_history_in_db(giver, receiver, count):
    sql = """INSERT INTO history (giver, receiver, count, timestamp)
             VALUES (%s, %s, %s, %s)"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, (str(giver), str(receiver), count, time.time()))
    conn.commit()
    cur.close()

def update_user_count_in_db(giver_id, receiver_id, username_present, count):
    sql = """INSERT INTO users (user_id, username_present, received_swats_count)
             VALUES (%s, %s, %s)
             ON CONFLICT (user_id) 
             DO UPDATE 
                SET received_swats_count = users.received_swats_count + %s
                RETURNING received_swats_count;"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, (str(receiver_id), username_present, count, count))
    conn.commit()
    cur.close()
    update_history_in_db(giver_id, receiver_id, count)

def get_user_count_from_db(user_id):
    sql = """SELECT users.received_swats_count 
             FROM users
             WHERE users.user_id=%s"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, (str(user_id),))
    result = None
    if cur.rowcount == 1:
        result = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return result

def should_rate_limit_per_person(giver, receiver):
    rate_limit = env_vars["PER_PERSON_TIME_LIMIT"]
    if rate_limit == 0:
        return False
    sql = """SELECT MAX(timestamp) FROM history
             WHERE giver = %s AND receiver = %s;"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, (str(giver), str(receiver)))
    result = None
    if cur.rowcount == 1:
        result = cur.fetchone()[0]
    conn.commit()
    cur.close()
    if not result:
        return False
    return time.time() - result < rate_limit*60

def should_rate_limit_for_anyone(giver):
    rate_limit = env_vars["TIME_WINDOW"]
    if rate_limit == 0:
        return False
    sql = """SELECT timestamp FROM history
             WHERE giver = %s
             ORDER BY timestamp DESC;"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, (str(giver),))
    if cur.rowcount < env_vars["TIME_WINDOW_LIMIT_COUNT"]:
        return False
    limit_result = cur.fetchmany(env_vars["TIME_WINDOW_LIMIT_COUNT"])[env_vars["TIME_WINDOW_LIMIT_COUNT"] - 1][0]
    conn.commit()
    cur.close()
    return time.time() - limit_result < rate_limit*60
