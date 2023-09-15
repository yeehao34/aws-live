from flask import Flask, render_template, request
from pymysql import connections
import os
# import boto3
from config import *

app = Flask(__name__, template_folder='template/dist', static_folder="template/dist/assets")

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,  
    user=customuser,
    password=custompass,
    db=customdb
)

output = {}
studentTable = 'student'
companyTable = 'company'
staffTable = 'staff'
jobTable = 'job'

@app.route("/")
def home():
    return render_template('login.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
