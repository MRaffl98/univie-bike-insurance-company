import flask_login
import mysql.connector
from data_generator import DataGenerator

mysql_config = {
    'user': 'user',
    'password': 'password',
    'host': 'sql',
    'port': '3306',
    'database': 'imse_sql_db'
}

conn = mysql.connector.connect(**mysql_config)

def create_database(): 
    try:
        # create a cursor
        cursor = conn.cursor()

        # drop tables if they exist
        with open('sql/drop.sql', 'r') as file:
            drop_file = file.read()
        drop_statements = drop_file.split(';')
        for statement in drop_statements:
            cursor.execute(statement)
    
        # create tables
        with open('sql/init.sql', 'r') as file:
            create_file = file.read()
        create_statements = create_file.split(';')
        for statement in create_statements:
            cursor.execute(statement)
        
        return False

    except Exception as e:
        return True

    finally:
        if conn.is_connected():
            cursor.close()


def fill_database():
    try:
        # create a cursor
        cursor = conn.cursor()

        # generate random data
        data_generator = DataGenerator(agent_count = 5, customer_count = 50, random_state = 2021)
        data_generator.generate_database()

        # insert data into db   
        statement = "INSERT INTO user (first_name, last_name, email, pass_word) VALUES (%s, %s, %s, %s)"
        cursor.executemany(statement, data_generator.users)
        conn.commit()
        
        statement = "INSERT INTO agent (user_id, salary, career_level) VALUES (%s, %s, %s)"
        cursor.executemany(statement, data_generator.agents)
        conn.commit()

        statement = "INSERT INTO customer (user_id, birthdate, country, zip, town, street, street_number, entry_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.executemany(statement, data_generator.customers)
        conn.commit()

        statement = "INSERT INTO policy (user_id, frame_number, replacement_value, contract_start_date) VALUES (%s, %s, %s, %s)"
        cursor.executemany(statement, data_generator.policies)
        conn.commit()

        statement = "INSERT INTO options (option_name, replacement_value_loading, base_loading, recommended_by) VALUES (%s, %s, %s, %s)"
        cursor.executemany(statement, data_generator.options)
        conn.commit()

        statement = "INSERT INTO policy_options (policy_id, option_id, fee) VALUES (%s, %s, %s)"
        cursor.executemany(statement, data_generator.policy_options)
        conn.commit()

        statement = "INSERT INTO claim (policy_id, claim_id, option_id, claim_description, claim_date, loss) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.executemany(statement, data_generator.claims)
        conn.commit()

        return False

    except Exception as e:
        return True
    
    finally:
        if conn.is_connected():
            cursor.close()


def get_feereport_sql(filter=1):
    try:
        cursor = conn.cursor()
        statement = f"""
                    SELECT * FROM (
                        SELECT  user.user_id AS id, 
                                user.last_name AS lastname,
                                user.first_name AS firstname, 
                                SUM(CASE WHEN options.option_id = 1 THEN policy_options.fee END) AS theft,
                                SUM(CASE WHEN options.option_id = 2 THEN policy_options.fee END) AS vandalism,
                                SUM(CASE WHEN options.option_id = 3 THEN policy_options.fee END) AS fire,
                                SUM(CASE WHEN options.option_id = 4 THEN policy_options.fee END) AS loss,
                                SUM(CASE WHEN options.option_id = 5 THEN policy_options.fee END) AS robbery,
                                SUM(policy_options.fee) AS total, 
                                COUNT(DISTINCT policy.policy_id) AS policycount
                        
                        FROM    policy_options
                                INNER JOIN options  ON policy_options.option_id = options.option_id
                                INNER JOIN policy   ON policy_options.policy_id = policy.policy_id
                                INNER JOIN user ON policy.user_id = user.user_id

                        WHERE policy.contract_end_date IS NULL OR policy.contract_end_date > CURRENT_DATE()
                        GROUP BY user.user_id
                        ORDER BY user.last_name
                    ) subquery
                    WHERE policycount >= {filter}
                    """
        cursor.execute(statement)
        result = cursor.fetchall()

        # replace None values for pretty printing
        result = [tuple("-" if val is None else val for val in tup) for tup in result]
        
    except Exception as e:
        result = str(e)

    finally:
        if conn.is_connected():
            cursor.close()
        return result

def get_claimreport_sql(filter=0):
    try:
        cursor = conn.cursor()
        statement = f"""
                    SELECT * FROM (
                        SELECT  user.user_id AS id, 
                                user.last_name AS lastname,
                                user.first_name AS firstname, 
                                COUNT(DISTINCT policy.policy_id) AS policycount,
                                COUNT(DISTINCT CASE WHEN 
                                    policy.contract_end_date IS NULL OR policy.contract_end_date > CURRENT_DATE()
                                    THEN policy.policy_id ELSE NULL END) AS activepolicies,
                                COUNT(CASE WHEN claim.claim_id IS NOT NULL THEN 1 ELSE NULL END) AS claimcount,
                                SUM(claim.loss) AS totalloss,
                                MAX(claim.claim_date) as lastclaim                               
                        
                        FROM    user
                                INNER JOIN policy ON user.user_id = policy.user_id
                                LEFT JOIN claim ON policy.policy_id = claim.policy_id       /* ALTERNATIVE: INNER JOIN */

                        /* ADD WHERE AT LEAST ONE ACTIVE POLICY? AS NESTED QUERY */

                        GROUP BY user.user_id
                        ORDER BY user.last_name
                    ) subquery
                    """
        statement = statement if filter==0 else statement + f" WHERE totalloss >= {filter}"
        cursor.execute(statement)
        result = cursor.fetchall()

        # replace None values for pretty printing
        result = [tuple("-" if val is None else val for val in tup) for tup in result]
        
    except Exception as e:
        result = str(e)

    finally:
        if conn.is_connected():
            cursor.close()
        return result

def init_user():
     try:
        cursor = conn.cursor()
        curr_user = flask_login.current_user.id
        sql = f'SELECT * FROM policy  WHERE policy.user_id = {curr_user}' 
        cursor.execute(sql)
        policies = cursor.fetchall()
    
     finally:
        if conn.is_connected():
            cursor.close()
        return policies

def write_policy(UserID, FrameNumber, ReplacementValue, contract_start, contract_end, offer): 
    try:
        cursor = conn.cursor()
        sql = 'INSERT INTO policy (user_id, frame_number, replacement_value, contract_start_date) VALUES (%s,%s, %s, %s)'
        val = (UserID, FrameNumber, ReplacementValue, contract_start)
        cursor.execute(sql, val)
        policy_id = str(cursor.lastrowid)
        conn.commit()
        
        all_policies = ""


        cursor = conn.cursor()
        sql2 = "INSERT INTO policy_options (policy_id, option_id, fee) VALUES (%s, %s, %s)"
        val2 = []
        
        for i in range(len(offer)):
            o_id = str(offer[i][0])
            fee = str(offer[i][1])
            val_single = (policy_id, o_id, fee)
            val2.append(val_single)
        
        cursor.executemany(sql2, val2)
        conn.commit()

        curr_user = flask_login.current_user.id
        sql = f'SELECT * FROM policy WHERE policy.user_id = {curr_user}' 
        cursor.execute(sql)
        all_policies = cursor.fetchall()

    finally:
        if conn.is_connected():
            cursor.close()
        return all_policies

def write_claim(policy_id, claim_description, claim_date, loss): 
    try:
        cursor = conn.cursor()
        sql = f'SELECT * FROM claim WHERE claim.policy_id = {policy_id}'
        cursor.execute(sql)
        n_claims = cursor.fetchall()
        n = 0 
        if n_claims:
            for i in n_claims: 
                n += 1
        sql = 'INSERT INTO claim (policy_id, claim_id, claim_description, claim_date, loss) VALUES (%s, %s, %s, %s, %s)'
        val = (policy_id, n+1, claim_description, claim_date, loss)
        cursor.execute(sql, val)
        conn.commit()

        sql = f'SELECT * FROM claim WHERE claim.policy_id = {policy_id}'
        cursor.execute(sql)
        n_claims = cursor.fetchall()

    finally:
            if conn.is_connected():
                cursor.close()
            return n_claims

def init_claim(policy_id):
     try:
        cursor = conn.cursor()
        sql = f'SELECT * FROM claim WHERE claim.policy_id = {policy_id}'
        cursor.execute(sql)
        n_claims = cursor.fetchall()
    
     finally:
        if conn.is_connected():
            cursor.close()
        return n_claims