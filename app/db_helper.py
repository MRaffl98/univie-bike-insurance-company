from sql_helper import get_feereport_sql, get_claimreport_sql, init_user_sql, write_policy_sql, write_claim_sql, init_claim_sql, conn
from mongo_helper import get_feereport_mongo, get_claimreport_mongo, init_user_mongo, write_policy_mongo, write_claim_mongo, init_claim_mongo, mongo_user
import mysql.connector

def get_feereport(filter=1, mongo=False):
    if mongo:
        return get_feereport_mongo(filter)
    else:
        return get_feereport_sql(filter)


def get_claimreport(filter=0, mongo=False):
    if mongo:
        return get_claimreport_mongo(filter)
    else:
        return get_claimreport_sql(filter)


def init_user(mongo):
    if mongo:
        return init_user_mongo()
    else:
        return init_user_sql()


def write_policy(UserID, FrameNumber, ReplacementValue, contract_start, contract_end, offer, lastname, mongo):
    if mongo:
        return write_policy_mongo(UserID, FrameNumber, ReplacementValue, contract_start, contract_end, offer, lastname)
    else:
        return write_policy_sql(UserID, FrameNumber, ReplacementValue, contract_start, contract_end, offer)


def write_claim(policy_id, claim_description, claim_date, loss, mongo): 
    if mongo:
        return write_claim_mongo(policy_id, claim_description, claim_date, loss)
    else:
        return write_claim_sql(policy_id, claim_description, claim_date, loss)


def init_claim(policy_id, mongo):
    if mongo:
        return init_claim_mongo(policy_id)
    else:
        return init_claim_sql(policy_id)

def get_user(id, mongo): 
    if mongo: 
        result = mongo_user.find_one({"_id": id}, {"first_name": 1, 'last_name': 1})
        first_name = result['first_name']
        last_name = result['last_name']
        return first_name, last_name
    else: 
        mysql_config = {
        'user': 'user',
        'password': 'password',
        'host': 'sql',
        'port': '3306',
        'database': 'imse_sql_db'
    }
        conn = mysql.connector.connect(**mysql_config)
        try: 
            cursor = conn.cursor()
            statement = f"SELECT first_name, last_name FROM user WHERE user_id = {int(id)}"
            cursor.execute(statement)
            result = cursor.fetchone()
            first_name = result[0]
            last_name = result[1]
            cursor.close()
        finally: 
             return first_name, last_name


        