from flask import Flask, jsonify, request, make_response
from pymongo import MongoClient
from flask_cors import CORS
from pymongo.server_api import ServerApi
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)
uri = "mongodb+srv://pokefun:rliiTFpEjM0zeTIf@pokefun.hglcxgo.mongodb.net/?retryWrites=true&w=majority&appName=PokeFun"
client = MongoClient(uri, server_api=ServerApi('1'))  # Connect to the MongoDB cluster
db = client['Pokemon']
collectionPokemon = db['Pokemon']
collectionUsers = db['Users']
CORS(app, resources={r"/*": {"origins": "https://poke-fun-blush.vercel.app"}})

SECRET_KEY = "oU7ufaHTqk7lE0OM7as5Kl1AY43G7UfO"

def generate_jwt(username):
    payload = {
        'exp': datetime.utcnow() + timedelta(days=0, minutes=30),
        'iat': datetime.utcnow(),
        'sub': username
    }
    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm='HS256'
    )

def extract_username(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

@app.route('/registerUser', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'result': 'error', 'details': 'Username or password not provided'})

    existing_user = collectionUsers.find_one({'username': username})

    if existing_user is not None:
        return jsonify({'result': 'error', 'details': 'Username already registered'})

    try:
        result = collectionUsers.insert_one({'username': username, 'password': password})

        # Generate a JWT token for the new user
        token = generate_jwt(username)

        # Create a response
        response = make_response(jsonify({'result': 'success', 'details': 'User registered'}))

        # Set the JWT token as an HttpOnly cookie
        response.set_cookie('token', token, httponly=True)

        return response
    except Exception as e:
        # Handle errors gracefully
        return jsonify({'result': 'error', 'details': str(e)})

@app.route('/loginUser', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'result': 'error', 'details': 'Username or password not provided'})

    existing_user = collectionUsers.find_one({'username': username, 'password': password})

    if existing_user is None:
        return jsonify({'result': 'error', 'details': 'Invalid username or password'})

    try:
        # Generate a JWT token for the user
        token = generate_jwt(username)

        # Create a response
        response = make_response(jsonify({'result': 'success', 'details': 'Logged in'}))

        # Set the JWT token as an HttpOnly cookie
        response.set_cookie('token', token, httponly=True)

        return response
    except Exception as e:
        # Handle errors gracefully
        return jsonify({'result': 'error', 'details': str(e)})

# Define other routes and functions here...

if __name__ == "__main__":
    app.run(debug=True)  # You might want to remove debug=True in production
