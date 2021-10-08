from select import select
from sqlite3 import Connection as SQLite3Connection
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.engine import Engine
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import linked_list


# app
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sqlitedb.file"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = 0


# configure sqlite3 to enforce foreign key contraints
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


db = SQLAlchemy(app)
now = datetime.now()


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50))
    worksite = db.relationship("Worksite", cascade="all, delete")
    equipment = db.relationship("Equipment", cascade="all, delete")


class Worksite(db.Model):
    __tablename__ = "worksite"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Equipment(db.Model):
    __tablename__ = "equipment"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    working_hour = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    worksite_id = db.Column(db.Integer, db.ForeignKey("worksite.id"), nullable=False)


# routes
@app.route("/user", methods=["POST"])
def create_user():
    data = request.get_json()
    new_user = User(
        name=data["name"],
        email=data["email"]
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created"}), 200


@app.route("/<user_id>/worksite", methods=["POST"])
def create_worksite(user_id):
    data = request.get_json()

    # check user if not exist
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"message": "user does not exist!"}), 400

    new_worksite = Worksite(
        name=data["name"],
        user_id=user_id

    )
    db.session.add(new_worksite)
    db.session.commit()
    return jsonify({"message": "Worksite created"}), 200


@app.route("/<user_id>/<worksite_id>/equipment", methods=["POST"])
def create_equipment(user_id, worksite_id):
    data = request.get_json()

    # check user if not exist
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"message": "user does not exist!"}), 400

    worksite = User.query.filter_by(id=worksite_id).first()
    if not worksite:
        return jsonify({"message": "worksite does not exist!"}), 400

    new_equipment = Equipment(
        name=data["name"],
        working_hour=data["working_hour"],
        user_id=user_id,
        worksite_id=worksite_id

    )
    db.session.add(new_equipment)
    db.session.commit()
    return jsonify({"message": "Equipment created"}), 200


@app.route("/<user_id>/worksite", methods=["GET"])
def get_worksite(user_id):
    worksite = Worksite.query.filter_by(user_id=user_id)

    return_list = list()
    for post in worksite:
        return_list.append(
            {
                "id": post.id,
                "name": post.name
            }
        )

    if not post:
        return jsonify({"message": "post not found"})

    return jsonify(return_list)


@app.route("/<user_id>/equipment/<worksite_id>", methods=["GET"])
def get_equipment(user_id, worksite_id):
    equipment = Equipment.query.filter_by(user_id=user_id, id=worksite_id)
    return_list = list()
    for post in equipment:
        return_list.append(
            {
                "id": post.id,
                "working_hour": post.working_hour,
                "user_id": post.user_id
            }
        )

    return jsonify(return_list)


@app.route("/equipment/descending_working_hour/<user_id>", methods=["GET"])
def get_equipment_descending(user_id):
    equipments = Equipment.query.order_by(Equipment.working_hour).filter_by(user_id=user_id).all()
    all_equipments_ll = linked_list.LinkedList()

    for equipment in equipments:
        all_equipments_ll.insert_beginning(
            {
                "id": equipment.id,
                "name": equipment.name,
                "working_hour": equipment.working_hour,
                "worksite_id": equipment.worksite_id

            }
        )

    return jsonify(all_equipments_ll.to_list()), 200


if __name__ == "__main__":
    app.run(debug=True)

