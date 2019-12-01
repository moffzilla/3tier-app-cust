from flask import Flask, jsonify, request
from gevent import monkey
monkey.patch_all()
import requests
import json
from caspyr import Session, Deployment, Project, User, Blueprint, CloudAccount
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_socketio import SocketIO, emit
from threading import Thread


app = Flask(__name__)

app.secret_key = "super secret key"
socketio = SocketIO(app)
CORS(app)
thread = None

@app.route("/api/post", methods=["POST"])
def insert_post():
    req = request.get_json()
    _title = req['title']
    _text = req['text']
    conn = psycopg2.connect("host=db dbname=posts user=postgres password=postgres_password")
    cur = conn.cursor()
    cur.execute("INSERT INTO textData (title, text) VALUES (%s, %s)", (_title, _text))
    conn.commit()
    print("Data push happening now")
    cur = conn.cursor(cursor_factory=RealDictCursor)
    data = cur.execute('SELECT * FROM textData ORDER BY id DESC')
    test = cur.fetchall()
    print(test)
    socketio.emit('my event', test)
    return request.data

@app.route("/api/posts", methods=["GET"])
def get_posts():
    conn = psycopg2.connect("host=db dbname=posts user=postgres password=postgres_password")
    cur = conn.cursor(cursor_factory=RealDictCursor)
    data = cur.execute('SELECT * FROM textData ORDER BY id DESC')
    test = cur.fetchall()
    return jsonify(test)

@app.route("/api/health", methods=["GET"])
def get_health():
    stats = "{'status':'completed','platform':'healthy'}"
    return jsonify(stats)

@app.route("/api", methods=["POST"])
def get_data():
    req = request.get_json()
    token = req['cspapitoken']
    s = Session.login(token)
    serialData = {}
    deployments = len(Deployment.list(s))
    bps = len(Blueprint.list(s))
    projects = len(Project.list(s))
    cloudaccounts = len(CloudAccount.list(s))
    serialData['deployments'] = deployments
    serialData['bps'] = bps
    serialData['projects'] = projects
    serialData['cloudaccounts'] = cloudaccounts
    return jsonify(serialData)

@socketio.on('my event')
def handle_event(data):
    print('received')
    return jsonify(data)

@socketio.on('connected')
def handle_connect():
    while True:
        socketio.sleep(3)
        print('connected')


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True, port=80)
