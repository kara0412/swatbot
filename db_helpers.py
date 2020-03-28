import time
from collections import defaultdict

import psycopg2

from settings import ENV, DATABASE_URL, PER_PERSON_TIME_LIMIT

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
in_memory_swat_count_dict = defaultdict(int)

def _env_is_test():
    return ENV == 'TEST'

def reset_dict():
    in_memory_swat_count_dict.clear()

def update_history_in_db(giver, receiver, count):
    if _env_is_test():
        return
    sql = """INSERT INTO history (giver, receiver, count, timestamp)
             VALUES (%s, %s, %s, %s)"""
    cur = conn.cursor()
    cur.execute(sql, (str(giver), str(receiver), count, time.time()))
    conn.commit()
    cur.close()


def update_user_count_in_db(giver_id, receiver_id, username_present, count):
    if _env_is_test():
        in_memory_swat_count_dict[receiver_id] += count
        return
    sql = """INSERT INTO users (user_id, username_present, received_swats_count)
             VALUES (%s, %s, %s)
             ON CONFLICT (user_id) 
             DO UPDATE 
                SET received_swats_count = users.received_swats_count + %s
                RETURNING received_swats_count;"""
    cur = conn.cursor()
    cur.execute(sql, (str(receiver_id), username_present, count, count))
    conn.commit()
    cur.close()
    update_history_in_db(giver_id, receiver_id, count)

def get_user_count_from_db(user_id):
    if _env_is_test():
        return in_memory_swat_count_dict[user_id]
    sql = """SELECT users.received_swats_count 
             FROM users
             WHERE users.user_id=%s"""
    cur = conn.cursor()
    cur.execute(sql, (str(user_id),))
    result = None
    if cur.rowcount == 1:
        result = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return result

def should_rate_limit(giver, receiver):
    if _env_is_test():
        return False
    sql = """SELECT MAX(timestamp) FROM history
             WHERE giver = %s AND receiver = %s;"""
    cur = conn.cursor()
    cur.execute(sql, (str(giver), str(receiver)))
    result = None
    if cur.rowcount == 1:
        result = cur.fetchone()[0]
    conn.commit()
    cur.close()
    if not result:
        return False
    return time.time() - result < PER_PERSON_TIME_LIMIT*60