CREATE TABLE IF NOT EXISTS user (
	user_id int unsigned NOT NULL AUTO_INCREMENT,
	first_name varchar(100) NOT NULL,
	last_name varchar(100) NOT NULL,
	email varchar(100) NOT NULL UNIQUE,
	pass_word varchar(100) NOT NULL,
	PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS agent (
	user_id int unsigned NOT NULL,
	salary decimal(8, 2) unsigned NOT NULL, 
	career_level int unsigned NOT NULL,
	PRIMARY KEY (user_id),
	FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
); 

CREATE TABLE IF NOT EXISTS customer (
	user_id int unsigned NOT NULL,
	birthdate date NOT NULL,
	country varchar(100) NOT NULL,
	zip varchar(100) NOT NULL,
	town varchar(100) NOT NULL,
	street varchar(100) NOT NULL,
	street_number varchar(100) NOT NULL,
	entry_date date NOT NULL,
	PRIMARY KEY (user_id),
	FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS policy (
	policy_id int unsigned NOT NULL AUTO_INCREMENT,
	user_id int unsigned,
	frame_number varchar(100) NOT NULL,
	replacement_value decimal(8, 2) unsigned NOT NULL,
	contract_start_date date NOT NULL,
	contract_end_date date DEFAULT NULL,
	CHECK (contract_end_date IS NULL OR contract_end_data > contract_start_date),
	PRIMARY KEY (policy_id),
	FOREIGN KEY (user_id) REFERENCES customer(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS options (
	option_id int unsigned NOT NULL AUTO_INCREMENT,
	option_name varchar(100) NOT NULL,
	replacement_value_loading decimal(6, 2) unsigned NOT NULL,
	base_loading decimal(6, 2) unsigned NOT NULL,
	recommended_by int unsigned, 
 	PRIMARY KEY (option_id),
	FOREIGN KEY (recommended_by) REFERENCES options(option_id)
);

CREATE TABLE IF NOT EXISTS policy_options (
	policy_id int unsigned NOT NULL,
	option_id int unsigned NOT NULL,
	fee decimal(8, 2) unsigned NOT NULL,
	PRIMARY KEY (policy_id, option_id),
	FOREIGN KEY (policy_id) REFERENCES policy(policy_id),
	FOREIGN KEY (option_id) REFERENCES options(option_id)
);

CREATE TABLE IF NOT EXISTS claim (
	policy_id int unsigned NOT NULL,
	claim_id int unsigned NOT NULL,
	option_id int unsigned NOT NULL DEFAULT '6',
	claim_description varchar(1000),
	claim_date date NOT NULL,
	loss decimal(8, 2) NOT NULL,
	claim_status varchar(100) NOT NULL DEFAULT 'reported',
	PRIMARY KEY (policy_id, claim_id),
	FOREIGN KEY (policy_id) REFERENCES policy(policy_id) ON DELETE CASCADE,
	FOREIGN KEY (option_id) REFERENCES options(option_id)
)

