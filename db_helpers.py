import time
from collections import defaultdict

import psycopg2

from settings import env_vars

in_memory_swat_count_dict = defaultdict(int)


def get_conn():
    return psycopg2.connect(env_vars["DATABASE_URL"], sslmode='require')

def has_voted(user_id):
    sql = """SELECT * FROM history WHERE giver='vote_resolver' and receiver=%s"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, (str(user_id),))
    return cur.rowcount == 1

def update_history_in_db(giver, receiver, count):
    sql = """INSERT INTO history (giver, receiver, count, timestamp)
             VALUES (%s, %s, %s, %s)"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, (str(giver), str(receiver), count, time.time()))
    conn.commit()
    cur.close()

def update_user_count_in_db(receiver_id, username_present, count):
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

def get_all_users_from_db():
    sql = """SELECT users.user_id FROM users"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    return result

def username_is_present(user_id):
    sql = """SELECT users.username_present FROM users WHERE users.user_id=%s"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, (str(user_id),))
    result = None
    if cur.rowcount == 1:
        result = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return result

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

def get_nth_recent_swat_time(giver, receiver=None, n=1, count_must_inc=False):
    select = "SELECT timestamp from history"
    condition = " WHERE giver=%s"
    args = (str(giver), n-1)
    if receiver:
        condition += " and receiver=%s"
        args = (str(giver), str(receiver), n-1)
    if count_must_inc:
        condition += " and count > 0"
    rest = """ORDER BY timestamp DESC
              LIMIT 1 offset %s"""
    full_sql = select + '\n' + condition + '\n' + rest
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(full_sql, args)
    result = None
    if cur.rowcount == 1:
        result = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return result

def get_leaderboard_from_db(n):
    sql = """SELECT * FROM users 
             ORDER BY received_swats_count DESC LIMIT %s;"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, (str(n),))
    result = cur.fetchall()
    conn.commit()
    cur.close()
    return result
