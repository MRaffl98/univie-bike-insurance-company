from enum import unique
import pymongo
import flask_login
import datetime 
# create connection and database
mongo_client = pymongo.MongoClient('mongodb://user:password@mongo:27017/')
mongo_db = mongo_client['imse_mongo_db']


# create collections
mongo_option = mongo_db['option']
mongo_user = mongo_db['user']
mongo_policy = mongo_db['policy']

mongo_policy.create_index([('user_id', pymongo.ASCENDING)]) 
mongo_policy.create_index([('last_name', pymongo.ASCENDING), ('first_name', pymongo.ASCENDING)])
mongo_user.create_index([('email', pymongo.ASCENDING)], unique=True)


# use cases
def init_user_mongo(): 
    curr_user = int(flask_login.current_user.id)
    
    mongo_cursor = mongo_policy.find( {'user_id': curr_user }, {'_id': 1, 'last_name': 1, 'frame_number': 1, 'contract_end_date': 1} )
    mongo_list = []
    for value in mongo_cursor: 
        po_id = value['_id']
        last_name = value['last_name']
        frameN = value['frame_number']
        endD = value['contract_end_date']
        row = (po_id, last_name, frameN, endD)
        mongo_list.append(row)
    return mongo_list

def write_policy_mongo(userid, FrameNumber, ReplacementValue, contract_start, contract_end, offer, lastname):
    attribute_names = ['_id', 'user_id', 'frame_number', 'replacement_value', 'contract_start_date', 'contract_end_date', 'last_name', 'options', 'claims']
    option_names = ['option_id', 'fee']
    mongo_cursor = mongo_policy.find({})
    N = len([ele for ele in mongo_cursor if isinstance(ele, dict)])

    print(N)
    open_insert_list = []
    for i in range(len(offer)): 
        opt = (offer[i][0], offer[i][1])
        option_insert = {key:value for key, value in zip(option_names, opt)}
        open_insert_list.append(option_insert)

    values = [N+1, userid, FrameNumber, ReplacementValue, contract_start, 'None', lastname,  open_insert_list, []]
    policy_insert = {key:value for key, value in zip(attribute_names, values)}
    mongo_policy.insert(policy_insert)
    all_policies = init_user_mongo()
    return all_policies

def init_claim_mongo(policy_id): 
    
    mongo_cursor = mongo_policy.find( {'_id': int(policy_id)})

    mongo_list = []
    for value in mongo_cursor: 
        po_id = value['_id']
        claims= value['claims']
        for claim in claims: 
            claim_id = claim['claim_id']
            claim_date = claim['claim_date']
            claim_desc = claim['claim_description']
            claim_status = claim['claim_status']
            row = (po_id, claim_id, claim_date, claim_desc, claim_status)
            mongo_list.append(row)
    return mongo_list

def write_claim_mongo(policy_id, claim_description, claim_date, loss):
    attribute_names = ['claim_id', 'option_id', 'claim_description', 'claim_date', 'loss', 'claim_status']
    mongo_cursor = mongo_policy.find({'_id': int(policy_id)})
    i = 0
    for value in mongo_cursor: 
        claims = value['claims']
        for claim in claims: 
            i += 1
    values = [i+1, 6, claim_description, datetime.datetime.strptime(claim_date,'%Y-%m-%d'), loss, 'reported']
    claim_insert = {key:value for key, value in zip(attribute_names, values)}
    mongo_policy.update(
        { '_id': int(policy_id)}, 
        { '$push': { 'claims': claim_insert }}
    )

    all_policies = init_claim_mongo(policy_id)
    return all_policies


# reports
def get_claimreport_mongo(filter=0):
    pipeline = [
        {"$addFields": {"active": {"$not": {"$gt": ["$currentDate", "$contract_end_date"]}}}},
        {"$group": {
            "_id": "$user_id",
            "last_name": {"$first": "$last_name"},
            "first_name": {"$first": "$first_name"},
            "policies": {"$sum": 1},
            "active_policies": {"$sum": {"$cond": ["$active", 1, 0]}}, 
            "claims": {"$push": "$claims"}
        }},
        {"$addFields": {"claims": {"$reduce": {"input": "$claims", "initialValue": [], "in": {"$concatArrays": ["$$value", "$$this"]}}}}},
        {"$unwind": {"path": "$claims", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": "$_id",
            "last_name": {"$first": "$last_name"},
            "first_name": {"$first": "$first_name"},
            "policies": {"$first": "$policies"},
            "active_policies": {"$first": "$active_policies"},
            "claim_count": {"$sum": 1},
            "loss_sum": {"$sum": "$claims.loss"},
            "last_claim": {"$max": "$claims.claim_date"}
        }},
        {"$sort": {"last_name": 1, "first_name": 1}}
    ]

    # quantile filter if required
    if filter!=0:
        pipeline.append({"$match": {"loss_sum": {"$gte": float(filter)}}})

    # execute query
    result = list(mongo_policy.aggregate(pipeline))

    # process results
    result = [tuple(doc.values()) for doc in result]
    result = [tuple("-" if val is None or val==0 else val for val in tup) for tup in result]
    result = [tuple(val.date() if type(val)==datetime.datetime else val for val in tup) for tup in result]

    return result

def get_feereport_mongo(filter=1):
    pipeline = [
        {"$match": {"$expr": {"$not": {"$gt": ["$currentDate", "contract_end_date"]}}}},
        {"$group": {
            "_id": "$user_id",
            "last_name": {"$first": "$last_name"},
            "first_name": {"$first": "$first_name"},
            "policies": {"$sum": 1},
            "options": {"$push": "$options"}
        }},
        {"$addFields": {"options": {"$reduce": {"input": "$options", "initialValue": [], "in": {"$concatArrays": ["$$value", "$$this"]}}}}},
        {"$unwind": "$options"},
        {"$lookup": {
            "from": "option",
            "localField": "options.option_id",
            "foreignField": "_id",
            "as": "option_doc"
        }},
        {"$group": {
            "_id": "$_id",
            "last_name": {"$first": "$last_name"},
            "first_name": {"$first": "$first_name"},
            "theft": {"$sum": {"$cond": [{"$in": ["theft", "$option_doc.option_name"]}, "$options.fee", 0]}},
            "vandalism": {"$sum": {"$cond": [{"$in": ["vandalism", "$option_doc.option_name"]}, "$options.fee", 0]}},
            "fire": {"$sum": {"$cond": [{"$in": ["fire", "$option_doc.option_name"]}, "$options.fee", 0]}},
            "loss": {"$sum": {"$cond": [{"$in": ["loss", "$option_doc.option_name"]}, "$options.fee", 0]}},
            "robbery": {"$sum": {"$cond": [{"$in": ["robbery", "$option_doc.option_name"]}, "$options.fee", 0]}},
            "total": {"$sum": "$options.fee"},
            "policies": {"$first": "$policies"}
        }},
        {"$sort": {"last_name": 1, "first_name": 1}}
    ]

    if filter!=1:
        pipeline.append({"$match": {"policies": {"$gte": int(filter)}}})

    # execute query
    result = list(mongo_policy.aggregate(pipeline))

    # process results
    result = [tuple(doc.values()) for doc in result]
    result = [tuple("-" if val is None or val==0 else val for val in tup) for tup in result]

    return result