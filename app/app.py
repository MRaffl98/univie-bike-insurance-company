from re import I
from types import FrameType
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from sql_helper import create_database, fill_database 
from db_helper import get_feereport, get_claimreport, init_claim, init_user, write_claim, write_policy, get_user
from user_helper import get_user_sql, get_user_by_email, is_agent, get_user_mongo
from forms import LoginForm, CreatePolicyForm, Offer, CreateClaim
from datetime import date, timedelta
from numpy import quantile
from migrate import migrate_options, migrate_agents, migrate_customers, migrate_policies

app = Flask(__name__)
app.secret_key = b'OB\x93\x11H\xb6F\x96v~\xd2,`\x17\xc5A'

#global variables 
FN = ""
repVal = ""
policy_id = ""
is_mongo_migrated = None 

option_list = [
    ('theft',     0.005, 3, None),
    ('vandalism', 0.001, 2, 1),
    ('fire',      0.001, 1, None), 
    ('loss',      0.01,  0, 3),
    ('robbery',   0.001, 1, 1)
]


########## LOGIN MANAGER ##########
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id): 
    if is_mongo_migrated:
        return get_user_mongo(user_id)
    else:
        return get_user_sql(user_id) 


########## ROUTES ##########
@app.route('/filldb', methods=['GET', 'POST'])
def filldb():
    global is_mongo_migrated

    if request.method == 'POST':

        if 'fill_sql' in request.form:
            error = create_database()
            error += fill_database()
            is_mongo_migrated = False
            return render_template('filldb.html', title="Create and fill DB", error=error, is_mongo_migrated=is_mongo_migrated, temp="MySQL DB is ready to fire")

        elif 'fill_mongo' in request.form: 
            error = migrate_options()        
            error += migrate_agents()
            error += migrate_customers()
            error += migrate_policies()
            is_mongo_migrated = True
            return render_template('filldb.html', title="Create and fill DB", error=error, is_mongo_migrated=is_mongo_migrated, temp="MongoDB is ready to fire")

        #return render_template('filldb.html', title="Create and fill DB", error=error, is_mongo_migrated=is_mongo_migrated, temp="temp")
    return render_template('filldb.html', title="Create and fill DB", is_mongo_migrated=is_mongo_migrated)

########## LOGIN ##########
@app.route('/', methods=['GET', 'POST'])
def login():
    global is_mongo_migrated
    if current_user.is_authenticated:
        redirect(url_for('account'))
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data, mongo=is_mongo_migrated)
        if user is not None:
            if user.password == form.password.data:
                login_user(user)
                return redirect(url_for('account'))
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



########## REPORT 1 ##########
@app.route('/feereport', methods=['GET', 'POST'])
@login_required
def feereport():
    global is_mongo_migrated
    user_first, user_last = get_user(int(current_user.id), mongo=is_mongo_migrated)

    if is_agent(current_user, mongo=is_mongo_migrated):
        filter = 1
        result = get_feereport(filter=filter, mongo=is_mongo_migrated)
        max_policies = max([tup[-1] for tup in result])
        if request.method == 'POST':
            filter = request.form["feereportSelector"]
            result = get_feereport(filter=filter, mongo=is_mongo_migrated)
            return render_template('feereport.html', result=result, max_policies=max_policies, filter=filter, is_mongo_migrated=is_mongo_migrated, user_first=user_first, user_last=user_last)
        return render_template('feereport.html', result=result, max_policies=max_policies, filter=filter, is_mongo_migrated= is_mongo_migrated, user_first=user_first, user_last=user_last)
    else:
        return redirect('account')


########## REPORT 2 ##########
@app.route('/claimreport', methods=['GET', 'POST'])
@login_required
def claimreport():
    global is_mongo_migrated
    user_first, user_last = get_user(int(current_user.id), mongo=is_mongo_migrated)
    if is_agent(current_user, mongo=is_mongo_migrated):
        filter = 0
        result = get_claimreport(filter=filter, mongo=is_mongo_migrated)
        total_losses = [tup[-2] for tup in result if tup[-2] != "-"]
        total_losses = [float(val) for val in total_losses]
        if request.method == 'POST':
            filter = int(request.form["claimreportSelector"])
            lower_bound = 0 if filter==0 else quantile(total_losses, q=filter/100)
            result = get_claimreport(filter=lower_bound, mongo=is_mongo_migrated)
            return render_template('claimreport.html', result=result, filter=filter, is_mongo_migrated=is_mongo_migrated,user_first=user_first, user_last=user_last)
        return render_template('claimreport.html', result=result, filter=filter, is_mongo_migrated=is_mongo_migrated, user_first=user_first, user_last=user_last)
    else:
        return redirect('account')


########## USE CASE 1##########
@app.route('/claim', methods=['GET', 'POST'])
@login_required
def claim():
    global is_mongo_migrated
    global policy_id
    curr_user = int(current_user.id)
    user_first, user_last = get_user(curr_user, mongo=is_mongo_migrated)
    form = CreateClaim()
    n_claims = init_claim(policy_id, mongo=is_mongo_migrated)

    if request.method == 'POST':
        desc = request.form["Description"]
        dateofloss = request.form["Dateofloss"]
        lossineuro = request.form["lossineuro"]

        if 'submit' in request.form: 

            n_claims = write_claim(policy_id, desc, dateofloss, int(lossineuro), mongo=is_mongo_migrated)
            return render_template('claim.html', form=form, policy_id=policy_id, n_claims=n_claims, is_mongo_migrated=is_mongo_migrated, user_first=user_first, user_last=user_last)
            
        elif 'cancel' in request.form: 
            return redirect('account')

    return render_template('claim.html', form=form, policy_id=policy_id, n_claims=n_claims, is_mongo_migrated=is_mongo_migrated, user_first=user_first, user_last=user_last)

########## USE CASE 2##########
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    global is_mongo_migrated
    global curr_user
    has_offer=False
    user_first, user_last = get_user(int(current_user.id), mongo=is_mongo_migrated)
    
    if is_agent(current_user, mongo=is_mongo_migrated):
        if request.method == 'POST':
            if "feereport_button" in request.form:
                return redirect('feereport')
            elif "claimreport_button" in request.form:
                return redirect('claimreport')
        return render_template('agent.html', is_mongo_migrated=is_mongo_migrated, user_first=user_first, user_last=user_last)
    
    else:
        
        all_policies = init_user(mongo=is_mongo_migrated)
        form = CreatePolicyForm()
        form2= Offer()
        offer_print = []
        offer = []
        total_price = 0
       
        if request.method =='POST':
            

            if "submit" in request.form:
                global FN
                global repVal
                global options
                global option_list
        

                FN = request.form["FrameNumber"]
                repVal= request.form["ReplacementValue"]
                options = request.form.getlist("check")
    
                #prepare list for db insert
                offer = []
                for i in options: 
                    j = int(i)
                    offer_option = option_list[j-1][2] + float(repVal) * option_list[j-1][1]
                    offer.append((j, round(offer_option, 2)))

                #modify insert list for printing
                total_price = 0
                for option in offer:
                    option_id = option[0]
                    offer_print.append((option_list[option_id-1][0], option[1]))
                    total_price += option[1]
                #display offer 
                has_offer=True

            # offer appected --> write policy to db
            if "accept" in request.form:
                userid = current_user.id
                all_policies = write_policy(UserID=userid, FrameNumber=FN, ReplacementValue=repVal, contract_start=date.today().strftime('%Y-%m-%d'), contract_end= date.today()-timedelta(days=-2), offer=offer, lastname =user_last, mongo = is_mongo_migrated)
                flash('Thank you, your Policy has been accepted and added to the Database')
                offer = []
                offer_print = []
                total_price = 0
                return render_template('user.html', form=form, offer_print = offer_print, total_price = total_price, form2=form2, has_offer=has_offer, all_policies=all_policies, is_mongo_migrated=is_mongo_migrated, user_first=user_first, user_last=user_last)
            
            # offer appected --> write policy to db
            if "decline" in request.form:
                flash('Hate to see it')
                offer = []
                offer_print = []
                total_price = 0
            
            # button 'report a claim' clicked, redirect for claim request page
            if "report_claim" in request.form: 
                global policy_id
                policy_id = request.form.get('policy_id')
                return redirect('claim')
               
                    
        return render_template('user.html', form=form, form2=form2, offer = offer, offer_print = offer_print, total_price = total_price, has_offer=has_offer, all_policies=all_policies, is_mongo_migrated=is_mongo_migrated, user_first=user_first, user_last=user_last)

########## RUN APP ##########
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0' , ssl_context='adhoc')