import mysql.connector
from flask_login.mixins import UserMixin
from sql_helper import mysql_config, conn
from mongo_helper import mongo_user


class User(UserMixin):
    def __init__(self, id, email, pass_word):
        self.id = id
        self.email = email
        self.password = pass_word


def get_user_sql(user_id):
    try:
        cursor = conn.cursor()
        statement = f"SELECT user_id, email, pass_word FROM user WHERE user_id = {int(user_id)}"
        cursor.execute(statement)
        result = cursor.fetchone()
        if len(result) > 0:
            user = User(*result)
        else:
            user = None

    except Exception as e:
        user = None

    finally:
        if conn.is_connected():
            cursor.close()
        return user


def get_user_mongo(user_id):
    try:
        result = mongo_user.find_one({'_id': int(user_id)}, {"_id": 1, "email": 1, "pass_word": 1})
        if len(result) > 0:
            user = User(id=result["_id"], email=result["email"], pass_word=result["pass_word"])
        else:
            user = None

    except Exception as e:
        user = None

    finally:
        return user


def get_user_by_email(email, mongo):
    try:
        if mongo:
            result = mongo_user.find_one({"email": email}, {"_id": 1, "email": 1, "pass_word": 1})
            if len(result) > 0:
                user = User(id=result["_id"], email=result["email"], pass_word=result["pass_word"])
            else:
                user = None
        else:
            cursor = conn.cursor()
            statement = f"SELECT user_id, email, pass_word FROM user WHERE email = '{email}'"
            cursor.execute(statement)
            result = cursor.fetchone()
            if len(result) > 0:
                user = User(*result)
            else:
                user = None

    except Exception as e:
        user = None

    finally:
        if not mongo:
            if conn.is_connected():
                cursor.close()
        return user
  
    
def is_agent(user, mongo):
    try:
        if mongo:
            result = mongo_user.find_one({"_id": user.id}, {"is_agent": 1})
            value = bool(result["is_agent"])
        else:
            cursor = conn.cursor()
            statement = f"SELECT COUNT(*) FROM agent WHERE user_id = {user.id}"
            cursor.execute(statement)
            result = cursor.fetchone()
            if result[0] == 1:
                value = True
            else:
                value = False

    except Exception as e:
        value = False

    finally:
        if not mongo:
            if conn.is_connected():
                cursor.close()
        return value