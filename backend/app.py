from flask import Flask, request, jsonify, session, send_from_directory
import json, re, csv
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId
from bson.json_util import dumps, loads
import os
import datetime
from flask_mail import Message, Mail
from geopy.distance import geodesic
from math import radians, sin, cos, sqrt, atan2

from ML import recommend, add_event


load_dotenv()

app = Flask(__name__)
bcrypt = Bcrypt()
app.secret_key = os.environ.get("SECRET_KEY")

# MongoDB configuration
MONGO_URI = os.environ.get("MONGO_URI")
DATABASE_NAME = "infothon-vvce"

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
users_col = db["users"]
events_col = db["events"]
attendees_col = db["attendees"]

# Mail configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("EMAIL")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("EMAIL")
app.config["MAIL_PASSWORD"] = os.environ.get("APP_PASSWORD")
mail = Mail(app)


def parse_json(data):
    return json.loads(json.dumps(data, default=str))


def validate_password(password):
    # Password checker
    # Primary conditions for password validation:
    # Minimum 8 characters.
    # The alphabet must be between [a-z]
    # At least one alphabet should be of Upper Case [A-Z]
    # At least 1 number or digit between [0-9].
    # At least 1 character from [ _ or @ or $ ].

    # \s- Returns a match where the string contains a white space character
    if len(password) < 8 or re.search("\s", password):
        return False
    if not (
        re.search("[a-z]", password)
        and re.search("[A-Z]", password)
        and re.search("[0-9]", password)
    ):
        return False
    return True


# Registering to the application
@app.route("/api/signup", methods=["POST"])
def signup():
    # Get the signup data from the request
    data = request.get_json()

    # Validate the required fields
    required_fields = [
        "coordinates",
        "description",
        "name",
        "password",
        "confirmPassword",
        "languages",
        "topics",
        "email",
        "phone",
        "organization",
        "status",
        "industry",
        "age",
        "gender",
        "discoverable",
    ]
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400

    # Validate Password
    if not validate_password(data["password"]):
        return (
            jsonify(
                error="Password must contain atleast 8 characters, 1 uppercase, 1 lowercase, 1 number and 1 special character"
            ),
            400,
        )

    # Compare password with confirmPassword
    if data["password"] != data["confirmPassword"]:
        return jsonify(error="Passwords do not match"), 400

    if users_col.find_one({"email": data["email"]}) is not None:
        return jsonify(error="User already exists!"), 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    # Create a new user document
    user = {
        "coordinates": data["coordinates"],
        "description": data["description"],
        "name": data["name"],
        "password": hashed_password,
        "languages": data["languages"],
        "topics": data["topics"],
        "email": data["email"],
        "phone": data["phone"],
        "organization": data["organization"],
        "status": data["status"],
        "industry": data["industry"],
        "age": data["age"],
        "gender": data["gender"],
        "discoverable": data["discoverable"],
        "createdAt": datetime.datetime.utcnow(),
    }

    # Insert the user document into the users collection
    users_col.insert_one(user)

    # Send email to user
    subject = f"You're registered to 1Click, {data['name']}"
    body = "Your registeration is complete!\nLogin here http://localhost:3000/login to get started with 1Click!"

    # # Create the plain-text and HTML version of your message
    text = "Subject:" + subject + "\n" + body
    html = """
    <html>
    <body>
        <h2>Your registeration is complete!</h2>
        <p><em><a href="http://localhost:3000/login">Login here</a></em> to get started with 1Click!</p>
    </body>
    </html>
    """

    msg = Message()
    msg.subject = subject
    msg.recipients = [data["email"]]
    msg.body = text
    msg.html = html
    msg.sender = os.environ.get("EMAIL")
    mail.send(msg)

    return jsonify(message="Signup successful")


@app.route("/api/login", methods=["POST"])
def login():
    # Get the login data from the request
    data = request.get_json()

    # Validate the required fields
    required_fields = ["email", "password"]
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400

    # Retrieve the user document from the users collection
    user = users_col.find_one({"email": data["email"]})

    if user is None:
        return jsonify(error="User doesn't exist"), 400

    if user and bcrypt.check_password_hash(user["password"], data["password"]):
        # Store the entire user in the session
        # parse_json helps us deal with ObjectID in python
        session["user"] = parse_json(user)
        return parse_json(user), 200
    else:
        return jsonify(error="Invalid credentials"), 400


@app.route("/api/logout", methods=["POST"])
def logout():
    # Clear the user from the session
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 403
    session.pop("user", None)
    return jsonify(message="Logout successful")


# @app.route("/api/forgot-password", methods=["POST"])
# def forgot_password():
#     # Get the forgot password data from the request
#     data = request.get_json()

#     # Validate the required fields
#     required_fields = ["email"]
#     for field in required_fields:
#         if field not in data:
#             return jsonify(error=f"Missing required field: {field}"), 400

#     # Retrieve the user document from the users collection
#     user = users_col.find_one({"email": data["email"]})

#     if user:
#         # Reset the password logic here (e.g., send password reset email)
#         return jsonify(message="Password reset email sent")
#     else:
#         return jsonify(error="User not found")


@app.route("/api/create", methods=["POST"])
def create_event():
    # Get the event data from the request
    if not session.get("user"):
        return jsonify(error="Not logged in"), 403

    data = request.get_json()

    # Validate the required fields
    required_fields = [
        "description",
        "name",
        "language",
        "topics",
        "fields",
        "email",
        "phone",
        "status",
        "industry",
        "minAge",
        "maxAge",
        "startDate",
        "endDate",
        "coordinates",
        "venue",
        "location",
        "url",
        "genders",
    ]
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400

    # Create a new event document
    event = {
        "description": data["description"],
        "name": data["name"],
        "language": data["language"],
        "topics": data["topics"],
        "fields": data["fields"],
        "email": data["email"],
        "phone": data["phone"],
        "status": data["status"],
        "industry": data["industry"],
        "minAge": data["minAge"],
        "maxAge": data["maxAge"],
        "startDate": data["startDate"],
        "endDate": data["endDate"],
        "coordinates": data["coordinates"],
        "venue": data["venue"],
        "location": data["location"],
        "url": data["url"],
        "genders": data["genders"],
        "uid": data["uid"],
        "createdAt": datetime.datetime.utcnow(),
    }

    # Insert the event document into the events collection
    inserted_event = events_col.insert_one(event)
    id = inserted_event.inserted_id
    inserted_event = events_col.find_one({"_id": ObjectId(id)})
    add_event(inserted_event)
    return jsonify(message="Event created")



# @app.route("/api/update", methods=["PATCH"])
# def update_event():
#     data = request.get_json()
#     if not session.get("user"):
#         return jsonify(error="Not logged in"), 403

#     # Validate the required fields
#     # Validate the required fields
#     required_fields = [
#         "description",
#         "name",
#         "language",
#         "topics",
#         "fields",
#         "email",
#         "phone",
#         "status",
#         "industry",
#         "minAge",
#         "maxAge",
#         "startDate",
#         "endDate",
#         "coordinates",
#         "venue",
#         "location",
#         "url",
#         "genders",
#     ]


@app.route("/api/network")
def network():
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 403

    # print(session.get("user").get("email"), session["user"])
    query = {"email": {"$ne": session.get("user").get("email")}, "discoverable": True}
    networks = list(users_col.find(query))
    return parse_json(networks), 200


@app.route("/api/distance", methods=["POST"])
def calculate_distances():
    data = request.get_json()
    evnt_location_dict = data["location"]
    user_coord_dict = (session.get("user"))["coordinates"]
    user_coord = (user_coord_dict["latitude"], user_coord_dict["longitude"])
    evnt_location = (evnt_location_dict["latitudes"], evnt_location_dict["longitudes"])
    distance = geodesic(user_coord, evnt_location).kilometers

    return jsonify(distance=int(distance))


@app.route("/api/recommended")
def recommended():
    recommended_events = list(recommend((session.get("user"))["_id"], users_col))
    m = {"$match": {"_id": {"$in": recommended_events}}}
    a = {"$addFields": {"__order": {"$indexOfArray": [recommended_events, "$_id"]}}}
    s = {"$sort": {"__order": 1}}
    recommended_events = events_col.aggregate([m, a, s])
    final = []
    for event in recommended_events:
        final.append(event)
    return parse_json(final), 200


@app.route("/api/search", methods=["GET"])
def search_events():
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 403
    query = request.args.get("query")

    # Construct the search query
    search_query = {
        "$or": [
            {"name": {"$regex": query, "$options": "i"}},
            {"venue": {"$regex": query, "$options": "i"}},
            {"location": {"$regex": query, "$options": "i"}},
            {"topics": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
        ]
    }

    # Perform the search in the database
    events = list(events_col.find(search_query))
    return parse_json(events)


# Events listed by the user
@app.route("/api/list")
def list_events():
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 403

    query = {"uid": {"$eq": session.get("user").get("_id")}}
    events = list(events_col.find(query))
    return parse_json(events), 200


@app.route("/api/list-attendees/<eid>")
def list_attendees(eid):
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 403

    query = {"eid": eid}
    attendees = list(attendees_col.find(query))
    return parse_json(attendees), 200


@app.route("/api/get-attendees-csv/<eid>")
def get_attendees_csv(eid):
    # if not session.get("user"):
    #     return jsonify({"error": "Not logged in"}), 403

    query = {"eid": eid}
    attendees = list(attendees_col.find(query))
    # Create and open a file called "attendees.csv" in write mode
    filename = f"attendees-{eid}.csv"
    fields = events_col.find_one({"_id": ObjectId(eid)}, {"fields": 1, "_id": 0})
    with open(f"./attendees-store/{filename}", "w") as file:
        wobj = csv.writer(file)
        wobj.writerow(fields["fields"])
        for attendee in attendees:
            to_write = []
            for field in fields["fields"]:
                to_write.append(attendee[field])
            wobj.writerow(to_write)

    return send_from_directory(
        directory="./attendees-store", path=filename, as_attachment=True
    )


# Users registering for the event
@app.route("/api/register/<eid>", methods=["POST"])
def register(eid):
    # if not session.get("user"):
    data = request.get_json()
    print(data, data["isRegistered"])
    if data.get("email") and session.get("user") is None:
        email = attendees_col.find_one({"email": data.get("email"), "eid": eid})
        print("EMAILLLL ", email)
        if email is not None:
            return jsonify(error="Email already registered for the event!"), 400
    print("isRegistered ", data["isRegistered"])
    if data["isRegistered"] is True:
        # print("IN IF ", session.get("user").get("_id"), eid)
        fields = events_col.find_one({"_id": ObjectId(eid)}, {"fields": 1, "_id": 0})
        attendee_details = {}
        for field in fields["fields"]:
            attendee_details[field.lower()] = data[field]
        attendee_details["eid"] = eid
        if session.get("user"):
            attendee_details["uid"] = session.get("user").get("_id")  # or data["_id"]

        attendees_col.insert_one(attendee_details)
        return jsonify(fields), 201
    else:
        print("IN ELSE ", session.get("user").get("_id"), eid)
        print(
            attendees_col.find_one({"uid": session.get("user").get("_id"), "eid": eid})
        )
        if session.get("user"):
            attendees_col.delete_one(
                {"uid": session.get("user").get("_id"), "eid": eid}
            )
            return jsonify(message="Successfully unregistered"), 200


# Check if the user is registered
@app.route("/api/check-register/<eid>")
def check_register(eid):
    check = None
    if session.get("user"):
        check = attendees_col.find_one(
            {"eid": eid, "uid": session.get("user").get("_id")}
        )
        if check is None:
            return jsonify({"registered": False}), 200
        else:
            return jsonify({"registered": True}), 200
    return jsonify({"registered": False}), 200


# Implement this Afnan
@app.route("/api/my-events", methods=["GET"])
def my_events():
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 403

    attending_events = attendees_col.find({"uid": session.get("user").get("_id")})
    event_ids = [
        ObjectId(record["eid"]) for record in attending_events
    ]  # Extract event IDs from attending records

    attended_events = events_col.find(
        {"_id": {"$in": event_ids}}
    )  # Find events with matching IDs
    return parse_json(list(attended_events)), 200


@app.route("/api/events/<eid>", methods=["GET"])
def get_event(eid):
    event = events_col.find_one({"_id": ObjectId(eid)})
    return parse_json(event), 200


# Check if user's session exists
@app.route("/api/check-user")
def check_user():
    if session.get("user"):
        return parse_json({"exists": True, "user": session.get("user")}), 200
    return jsonify({"exists": False}), 200


# DEVROUTE: GET ALL DATA TO JSON. SHOULDN'T BE USED IN PRODUCTION
@app.route("/api/get-all-data/<collection_name>")
def get_all_data(collection_name):
    collection = db[collection_name]
    data = list(collection.find())
    return parse_json(data), 200


@app.route("/api/delete-attendee", methods=["DELETE"])
def delete_attendee():
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 403

    data = request.args.to_dict()
    print(data)
    print(attendees_col.find_one({"_id": ObjectId(data["_id"])}))
    attendees_col.delete_one({"_id": ObjectId(data["_id"])})
    return jsonify(message="Deleted Successfully"), 200


# @app.route("/api/delete-attendee", methods=["DELETE"])
# def delete_attendee():
#     if not session.get("user"):
#         return jsonify({"error": "Not logged in"}), 403

#     data = request.args.to_dict()
#     print(data)
#     print(attendees_col.find_one({"_id": ObjectId(data["_id"])}))
#     attendees_col.delete_one({"_id": ObjectId(data["_id"])})
#     return jsonify(message="Deleted Successfully"), 200


@app.route("/api/delete-event", methods=["DELETE"])
def delete_event():
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 403

    data = request.args.to_dict()
    print(data)
    print(events_col.find_one({"_id": ObjectId(data["_id"])}))
    events_col.delete_one({"_id": ObjectId(data["_id"])})
    attendees_col.delete_many({"eid": data["_id"]})
    return jsonify(message="Deleted Successfully"), 200


if __name__ == "__main__":
    app.run(debug=True)
