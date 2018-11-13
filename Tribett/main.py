from flask import Flask, render_template, request
import sqlalchemy as db
import json
import decimal, datetime

#Database connection and magic
engine = db.create_engine('mysql://root:@localhost:3306/tribett?unix_socket=/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock')
connection = engine.connect()
metadata = db.MetaData()
app = Flask(__name__)

clients = db.Table('clients', metadata, autoload=True, autoload_with=engine)
product_area = db.Table('product_area', metadata, autoload=True, autoload_with=engine)
features = db.Table('features', metadata, autoload=True, autoload_with=engine)

#For parsing sqlalchemy results to readable json
def alchemyencoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)

#@app.route("/index/<int:priority>", methods=["GET"]) #We created this fake route, just to test this method
def rePrioritize(old_priority):
    #The logic here is get the list of features
    #from the database that have a priority equal to or higher than
    #this new priority and update them with a simple increment in a
    #forloop
    features_update_query = db.select([features]).where(features.columns.priority >= old_priority).order_by(db.desc(features.columns.priority))
    features_update_res = connection.execute(features_update_query).fetchall()
    for feature in features_update_res:
        #We are incrementing the priority here
        new_priority = 0;
        new_priority = feature.priority + 1
        print(old_priority)
        print(feature.priority)
        print(new_priority)
        print("new_priority")
        update_query = db.update(features).values(priority = new_priority)
        update_query = update_query.where(features.columns.priority == old_priority)
        connection.execute(update_query)
    #return json.dumps({'status':'OK', 'message': 'success'});


#404 errors just because
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.route("/features/api/v1.0/add", methods=["POST"])
def add_feature():
    #Get values sent from ajax
    title = request.form["new_feature_request[0][title]"]
    desc = request.form["new_feature_request[0][desc]"]
    client = request.form["new_feature_request[0][client]"]
    area = request.form["new_feature_request[0][area]"]
    date = request.form["new_feature_request[0][date]"]
    priority = request.form["new_feature_request[0][priority]"]
    status = "not-started"

    #print(priority)
    rePrioritize(priority)

    query = db.insert(features).values(title = title, description = desc, priority=priority, target_date=date, product_area=area, client=client, status=status)
    connection.execute(query)

    features_query = db.select([features])
    features_res = connection.execute(features_query).fetchall()
    features_res_json = json.dumps([dict(r) for r in features_res], default=alchemyencoder)

    data = {"features": features_res_json}
    return json.dumps({'status':'OK', 'message': 'success', 'data': data});


@app.route("/")
def home():
    clients_query = db.select([clients.columns.name])
    clients_res = connection.execute(clients_query).fetchall()
    clients_res_json = json.dumps([dict(r) for r in clients_res], default=alchemyencoder)

    product_area_query = db.select([product_area.columns.name])
    product_area_res = connection.execute(product_area_query).fetchall()
    product_area_res_json = json.dumps([dict(r) for r in product_area_res], default=alchemyencoder)

    features_query = db.select([features])
    features_res = connection.execute(features_query).fetchall()
    features_res_json = json.dumps([dict(r) for r in features_res], default=alchemyencoder)

    data = {"clients": clients_res_json, "product_area": product_area_res_json, "features": features_res_json}
    return render_template("dashboard.html", data = data)

if __name__ == "__main__":
    app.run(debug=True)