import random
import names
import datetime as dt
import pandas as pd
from string import digits


# ========== HANDLE DATES ========== #
current_date = dt.datetime.now().date()
current_year = dt.datetime.now().year
earliest_birthdate = dt.date(1940, 1, 1)
latest_birthdate = current_date.replace(year = current_year - 20) # today - 20years

def generate_date(startdate, enddate):
    dayrange = (enddate-startdate).days
    random_days = random.randrange(dayrange)
    return startdate + dt.timedelta(days = random_days)

def str2date(datestring, format = '%Y-%m-%d'):
    return dt.datetime.strptime(datestring, format).date()

def date2str(date, format = '%Y-%m-%d'):
    return date.strftime(format)

# ========== ADDRESS ========== #
locations = {
    'Austria': pd.read_csv('./data/zipcodes.at.csv', usecols=[1,2]),
    'Germany': pd.read_csv('./data/zipcodes.de.csv', usecols=[1,2]),
    'Switzerland': pd.read_csv('./data/zipcodes.ch.csv', usecols=[1,2]),
    'Liechtenstein': pd.read_csv('./data/zipcodes.li.csv', usecols=[1,2])
}

streets = ['Hauptstrasse', 'Hauptallee', 'Berggasse', 'Rathausplatz', 'Schustergasse']

def generate_address(locations):
    country = random.choices(list(locations.keys()), weights=[0.8, 0.15, 0.04, 0.01], k=1)[0]
    zip_code, town = locations[country].iloc[random.randrange(locations[country].shape[0])]
    return (country, str(zip_code), town)

# ========== INSURANCE PRODUCTS ========== #
option_list = [
    ('theft',     0.005, 3, None),
    ('vandalism', 0.001, 2, 1),
    ('fire',      0.001, 1, None), 
    ('loss',      0.01,  0, 3),
    ('robbery',   0.001, 1, 1),
    ('undefined', 0,     0, None)
]

# ========== OTHER ========== #
mail_providers = ['@gmail.com', '@aon.at', '@gmx.at']
salary_range = (2000, 6000)


# ========== DATAGENERATOR CLASS ========== #
class DataGenerator:

    def __init__(self, agent_count = 10, customer_count = 100, random_state = 2021):
        self.agent_count = agent_count
        self.customer_count = customer_count
        self.user_count = agent_count + customer_count

        self.random_state = random_state

        self.users = None
        self.agents = None
        self.customers = None
        self.policies = None
        self.options = None
        self.policy_options = None
        self. claims = None

    # ========== USERS ========== #
        
    def create_user(self, is_agent = False):
        first_name = names.get_first_name()
        last_name = names.get_last_name()
        mail_provider = '@versicherung.at' if is_agent else random.choice(mail_providers)
        email = first_name + '.' + last_name + mail_provider
        pass_word = 'start123'
        return (first_name, last_name, email, pass_word)

    def create_users(self):
        user_list = []
        # generate data
        for i in range(self.agent_count):
            user = self.create_user(is_agent = True)
            user_list.append(user)
        for i in range(self.customer_count):
            user = self.create_user(is_agent = False)
            user_list.append(user)
        # store data
        self.users = user_list

    # ========== AGENTS ========== #    

    def create_agent(self, user_id):
        salary = random.randint(*salary_range)
        career_level = 1 + (salary - salary_range[0]) // ((salary_range[1] - salary_range[0]) / 10)
        return (user_id, salary, int(career_level))

    def create_agents(self):
        agent_list = []
        # generate data
        for i in range(self.agent_count):
            agent = self.create_agent(user_id = i+1)
            agent_list.append(agent)
        # store data
        self.agents = agent_list

    # ========== CUSTOMERS ========== #

    def create_customer(self, user_id):
        birthdate = generate_date(earliest_birthdate, latest_birthdate)
        country, zip_code, town = generate_address(locations)
        street = random.choice(streets)
        street_number = str(random.randint(1, 100))
        entry_date = generate_date(birthdate.replace(year = birthdate.year+18), current_date)
        return (user_id, date2str(birthdate), country, zip_code, town, street, street_number, date2str(entry_date))

    def create_customers(self):
        customer_list = []
        # generate data
        for i in range(self.customer_count):
            customer = self.create_customer(user_id = self.agent_count + i + 1)
            customer_list.append(customer)
        # store data
        self.customers = customer_list

    # ========== POLICIES ========== #

    def create_policy(self, user_id):
        frame_number = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=20))
        replacement_value = random.randint(50, 5000)
        customer_entry_date = str2date([x[-1] for x in self.customers if x[0] == user_id][0])
        contract_start_date = generate_date(customer_entry_date, current_date)
        return (user_id, frame_number, replacement_value, date2str(contract_start_date))

    def create_policies(self):
        policy_list = []
        # generate data
        for i in range(self.customer_count):
            user_id = self.agent_count + i + 1
            policy_count = random.choice([0, 1, 2])
            for _ in range(policy_count):
                policy = self.create_policy(user_id)
                policy_list.append(policy)
        # store data
        self.policies = policy_list

    # ========== OPTIONS ========== #

    def create_options(self):
        self.options = option_list

    # ========== POLICY OPTIONS ========== #

    def create_policy_option(self, policy_id):
        policy_option_list = []
        option_count = random.randint(1, len(self.options)-1)
        option_indices = list(set(random.choices(range(len(self.options)-1), k = option_count)))
        options = [self.options[i] for i in option_indices]
        for option, i in zip(options, option_indices):
            fee = option[2] + option[1] * self.policies[policy_id-1][2]
            policy_option_list.append((policy_id, i+1, round(fee, 2)))
        return policy_option_list

    def create_policy_options(self):
        policy_option_list = []
        # generate data
        for i in range(len(self.policies)):
            policy_option = self.create_policy_option(policy_id = i+1)
            policy_option_list.extend(policy_option)
        # store data
        self.policy_options = policy_option_list
            
    # ========== CLAIMS ========== #

    def create_claim(self, policy_id):
        claim_list = []
        existing_option_ids = [x[1] for x in self.policy_options if x[0] == policy_id]
        if len(existing_option_ids) > 0:
            claim_count = random.choices([0, 1, 2], weights = [0.45, 0.35, 0.2], k=1)[0]
            for i in range(claim_count):
                claim_id = i+1
                option_id = random.choice(existing_option_ids)
                claim_description = ''
                claim_date = generate_date(str2date(self.policies[policy_id-1][-1]), current_date)
                loss = random.randint(20, self.policies[policy_id-1][-2])
                claim_list.append((policy_id, claim_id, option_id, claim_description, date2str(claim_date), loss))
        return claim_list

    def create_claims(self):
        claim_list = []
        # generate data
        for i in range(len(self.policies)):
            claim = self.create_claim(policy_id = i+1)
            claim_list.extend(claim)
        # store data
        self.claims = claim_list

    # ========== WRAPPER ========== #

    def generate_database(self):
        random.seed(self.random_state)
        self.create_users()
        self.create_agents()
        self.create_customers()
        self.create_policies()
        self.create_options()
        self.create_policy_options()
        self.create_claims()
 
# ========== DEMO ========== #

if __name__ == "__main__":

    data_generator = DataGenerator(agent_count = 5, customer_count = 50, random_state = 2021)
    data_generator.generate_database()

    print('================ users ================')
    for user in data_generator.users:
        print(user)

    print('================ agents ================')
    for agent in data_generator.agents:
        print(agent)

    print('================ customers ================')
    for customer in data_generator.customers:
        print(customer)

    print('================ policies ================')
    for policy in data_generator.policies:
        print(policy)

    print('================ options ================')
    for option in data_generator.options:
        print(option)

    print('================ policy options ================')
    for policy_option in data_generator.policy_options:
        print(policy_option)

    print('================ claims ================')
    for claim in data_generator.claims:
        print(claim)