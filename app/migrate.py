from sql_helper import conn
from mongo_helper import mongo_option, mongo_user, mongo_policy
from decimal import Decimal
from datetime import date, datetime


########## HELPER FUNCTIONS ##########
def dec2num(result):
    return [tuple(float(x) if type(x)==Decimal else x for x in tup) for tup in result]

def date2datetime(result):
    return [tuple(datetime.combine(x, datetime.min.time()) if type(x) == date else x for x in tup) for tup in result]

def colnames(cursor):
   return [x[0] for x in cursor.description]


########## READ FUNCTIONS ##########
def read_options():
   return [x for x in mongo_option.find()]

def read_users():
    return [x for x in mongo_user.find()]

def read_policies():
    return [x for x in mongo_policy.find()]


########## MIGRATION FUNCTIONS ##########
def migrate_options():
    try:
        if conn.is_connected():
            # read in sql data
            cursor = conn.cursor()
            statement = "SELECT * FROM options"
            cursor.execute(statement)
            result = cursor.fetchall()

            # decimal to float for sql data
            result = dec2num(result)

            # handle column names
            attribute_names = colnames(cursor)
            attribute_names[0] = '_id'
            attribute_names = attribute_names[:-1] # delete recommended_by

            # initialize mongo insert object
            insert_list = []

            # create mongo insert data
            for tup in result:
                id = tup[0]
                insert_list.append({key:value for key, value in zip(attribute_names, tup[:-1])})
                recommends = [x[0] for x in result if x[-1] == id]
                if len(recommends) > 0:
                    insert_list[-1]["recommends"] = recommends

            # insert data into mongo
            result = mongo_option.insert_many(insert_list)

            return False

    except Exception as e:
        return True

    finally:
        if conn.is_connected():
            cursor.close()

def migrate_agents():
    try:
        if conn.is_connected():
            # read in sql data
            cursor = conn.cursor()
            statement = """
                        SELECT user.user_id, first_name, last_name, email, pass_word, salary, career_level 
                        FROM user 
                        INNER JOIN agent ON user.user_id = agent.user_id
                        """
            cursor.execute(statement)
            result = cursor.fetchall()

            # convert salary to float
            result = dec2num(result)

            # handle column names
            attribute_names = colnames(cursor)
            attribute_names[0] = "_id"

            # initialize mongo insert object
            insert_list = []

            # create insert data
            for tup in result:
                id = tup[0]
                insert_list.append({key:value for key, value in zip(attribute_names, tup)})
                insert_list[-1]["is_agent"] = True

            # insert data into mongo
            mongo_user.insert_many(insert_list)

            return False

    except Exception as e:
        return True

    finally:
        if conn.is_connected():
            cursor.close()

def migrate_customers():
    try:
        if conn.is_connected():
            # read in sql data
            cursor = conn.cursor()
            statement = """
                        SELECT  user.user_id, first_name, last_name, email, pass_word
                                birthdate, country, zip, town, street, street_number, entry_date
                        FROM user 
                        INNER JOIN customer ON user.user_id = customer.user_id
                        """
            cursor.execute(statement)
            result = cursor.fetchall()

            # convert salary to float
            result = dec2num(result)
            result = date2datetime(result)

            # handle column names
            attribute_names = colnames(cursor)
            attribute_names[0] = "_id"

            # initialize mongo insert object
            insert_list = []

            # create insert data
            for tup in result:
                id = tup[0]
                insert_list.append({key:value for key, value in zip(attribute_names, tup)})
                insert_list[-1]["is_agent"] = False

            # insert data into mongo
            mongo_user.insert_many(insert_list)

            return False

    except Exception as e:
        return True

    finally:
        if conn.is_connected():
            cursor.close()

def migrate_policies():
    try:
        if conn.is_connected():
            # read in policy data
            cursor = conn.cursor()
            statement = """
                        SELECT  policy_id, policy.user_id, frame_number, replacement_value, contract_start_date, contract_end_date,
                                user.first_name, user.last_name
                        FROM policy 
                        INNER JOIN user ON policy.user_id = user.user_id
                        """
            cursor.execute(statement)
            policy_result = cursor.fetchall()

            # process policy data
            policy_result = dec2num(policy_result)
            policy_result = date2datetime(policy_result)
            policy_names = colnames(cursor)
            policy_names[0] = "_id"

            # read in policy-options data
            statement = "SELECT * FROM policy_options"
            cursor.execute(statement)
            option_result = cursor.fetchall()

            # process options data
            option_result = dec2num(option_result)
            option_names = colnames(cursor)[1:]

            # read in claims data
            statement = "SELECT * FROM claim"
            cursor.execute(statement)
            claim_result = cursor.fetchall()

            # process claims data
            claim_result = dec2num(claim_result)
            claim_result = date2datetime(claim_result)
            claim_names = colnames(cursor)[1:]

            # initialize mongo insert object
            insert_list = []

            # create insert data
            for policy in policy_result:
                id = policy[0]
                insert_list.append({key:value for key, value in zip(policy_names, policy)})
                # add options
                options = [{key:val for key,val in zip(option_names, option[1:])} for option in option_result if option[0] == id]
                insert_list[-1]['options'] = options
                # add claims
                claims = [{key:val for key,val in zip(claim_names, claim[1:])} for claim in claim_result if claim[0] == id]
                insert_list[-1]['claims'] = claims

            # insert data into mongo
            mongo_policy.insert_many(insert_list)

            return False

    except Exception as e:
        return True

    finally:
        if conn.is_connected():
            cursor.close()