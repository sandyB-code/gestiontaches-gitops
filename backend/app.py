
import os
import socket

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)


# ============================================================
# Configuration PostgreSQL
# ============================================================
DATABASE_URI = os.environ.get("DATABASE_URI")

if not DATABASE_URI:
    raise RuntimeError(
        "La variable d'environnement DATABASE_URI est obligatoire."
    )

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ============================================================
# CORS
# ============================================================
CORS(app, resources={r"/tasks*": {"origins": "*"}})


# ============================================================
# Base de données
# ============================================================
db = SQLAlchemy(app)

# Flask-Migrate est conservé pour les migrations futures.
migrate = Migrate(app, db)


# Nom du pod backend qui traite la requête
POD = socket.gethostname()


# ============================================================
# Modèle Task
# ============================================================
class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))

    def as_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
        }


# ============================================================
# Initialisation de la base de données
# ============================================================
def init_database():
    """
    Crée les tables si elles n'existent pas encore.

    Les migrations Flask-Migrate pourront être utilisées
    ultérieurement lorsque nous mettrons en place le workflow
    de migration de la base.
    """
    with app.app_context():
        db.create_all()


# ============================================================
# GET /tasks
# ============================================================
@app.route("/tasks", methods=["GET"])
def get_tasks():
    items = Task.query.order_by(Task.id).all()

    return jsonify(
        {
            "pod": POD,
            "tasks": [task.as_dict() for task in items],
        }
    )


# ============================================================
# GET /tasks/<id>
# ============================================================
@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = db.session.get(Task, task_id)

    if task is None:
        abort(404, description="Tâche introuvable")

    return jsonify(
        {
            "pod": POD,
            "task": task.as_dict(),
        }
    )


# ============================================================
# POST /tasks
# ============================================================
@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True) or {}

    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()

    if not title:
        abort(400, description="Le champ 'title' est requis")

    task = Task(
        title=title,
        description=description,
    )

    db.session.add(task)
    db.session.commit()

    return (
        jsonify(
            {
                "pod": POD,
                "task": task.as_dict(),
            }
        ),
        201,
    )


# ============================================================
# PUT /tasks/<id>
# ============================================================
@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = db.session.get(Task, task_id)

    if task is None:
        abort(404, description="Tâche introuvable")

    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = str(data["title"]).strip()

        if not title:
            abort(
                400,
                description="Le champ 'title' ne peut pas être vide",
            )

        task.title = title

    if "description" in data:
        task.description = str(data["description"]).strip()

    db.session.commit()

    return jsonify(
        {
            "pod": POD,
            "task": task.as_dict(),
        }
    )


# ============================================================
# DELETE /tasks/<id>
# ============================================================
@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = db.session.get(Task, task_id)

    if task is None:
        abort(404, description="Tâche introuvable")

    db.session.delete(task)
    db.session.commit()

    return jsonify(
        {
            "pod": POD,
            "deleted": task_id,
        }
    )


# ============================================================
# GET /health
# ============================================================
@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "pod": POD,
        }
    )


# ============================================================
# Gestion des erreurs
# ============================================================
@app.errorhandler(400)
@app.errorhandler(404)
def handle_error(error):
    return (
        jsonify(
            {
                "error": error.description,
                "pod": POD,
            }
        ),
        error.code,
    )


# ============================================================
# Démarrage
# ============================================================
if __name__ == "__main__":
    init_database()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
    )

