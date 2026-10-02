import os
import socket

from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

DEFAULT_URI = (
    "postgresql://"
    "stateful-flask-user:stateful-flask-password@"
    "postgres.postgres.svc.cluster.local:5432/"
    "stateful-flask-db"
)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URI", DEFAULT_URI)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

POD = socket.gethostname()

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))

@app.route("/tasks", methods=["GET"])
def get_tasks():
    items = Task.query.all()
    return jsonify({
        "pod": POD,
        "tasks": [
            {"id": t.id, "title": t.title, "description": t.description}
            for t in items
        ],
    })

@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    task = Task(title=data["title"], description=data.get("description", ""))
    db.session.add(task)
    db.session.commit()
    return jsonify({
        "pod": POD,
        "task": {"id": task.id, "title": task.title, "description": task.description},
    }), 201

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "pod": POD})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
