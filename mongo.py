from flask import Flask, jsonify, request, make_response
from pymongo import MongoClient
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import jwt
from datetime import datetime, timedelta
#pip install flask
#pip install pymongo
#pip install flask_cors

app = Flask(__name__)
CORS(app)
uri = "mongodb+srv://pokefun:rliiTFpEjM0zeTIf@pokefun.hglcxgo.mongodb.net/?retryWrites=true&w=majority&appName=PokeFun"
client = MongoClient(uri,server_api=ServerApi('1')) # Connect to the MongoDB cluster
db = client['Pokemon']
collectionPokemon = db['Pokemon']
collectionUsers = db['Users']
CORS(app, supports_credentials=True, origins=['https://poke-fun-blush.vercel.app'])


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
    

@app.route('/saveHighscoreForHigherLower', methods=['POST'])
def saveHigherLowerHighscoreToMongo():
    data = request.get_json()
    token = request.cookies.get('token')  # Get the token from the cookies
    username = extract_username(token)
    score = data.get('score')

    if username is None:
        return jsonify({'result': 'error', 'details': 'No user logged in'})

    try:
        # Create a filter to find the user
        user_filter = {'username': username}

        # Fetch the user document
        user_doc = collectionUsers.find_one(user_filter)

        # If the user document doesn't exist, return an error
        if user_doc is None:
            return jsonify({'result': 'error', 'details': 'User does not exist'})

        # If 'gamedata' doesn't exist, initialize it as an empty array
        if 'gamedata' not in user_doc:
            collectionUsers.update_one(user_filter, {"$set": {'gamedata': [{'game': 'higherLower', 'score': score}]}})
            return jsonify({'result': 'success', 'score': score})

        # Find the index of the 'higherLower' game data
        game_index = next((index for index, game in enumerate(user_doc['gamedata']) if game['game'] == 'higherLower'), None)

        # If the 'higherLower' game data doesn't exist, add it
        if game_index is None:
            collectionUsers.update_one(user_filter, {"$push": {'gamedata': {'game': 'higherLower', 'score': score}}})
            return jsonify({'result': 'success', 'score': score})

        # If the new score is higher, update the score
        if user_doc['gamedata'][game_index]['score'] < score:
            collectionUsers.update_one(user_filter, {"$set": {f'gamedata.{game_index}.score': score}})
            return jsonify({'result': 'success', 'score': score})

        else:
            return jsonify({'result': 'success', 'details': 'Score is not higher than the current highscore'})

    except Exception as e:
        return jsonify({'result': 'error', 'details': 'Error saving highscore', 'error' : str(e)})
    

@app.route('/getHighscoreForHigherLower', methods=['GET'])
def getHighscoreForHigherLower():
    token = request.cookies.get('token')  # Get the token from the cookies
    username = extract_username(token)

    if username is None:
        return jsonify({'result': 'error', 'details': 'No user logged in'})

    try:
        # Create a filter to find the user
        user_filter = {'username': username}

        # Fetch the user document
        user_doc = collectionUsers.find_one(user_filter)

        # If the user document doesn't exist, return an error
        if user_doc is None:
            return jsonify({'result': 'error', 'details': 'User does not exist'})

        # Find the 'higherLower' game data
        higher_lower_game_data = next((game for game in user_doc['gamedata'] if game['game'] == 'higherLower'), None)

        # If the 'higherLower' game data doesn't exist, return an error
        if higher_lower_game_data is None:
            return jsonify({'result': 'error', 'details': 'No higherLower game data'})

        # Return the highscore
        return jsonify({'result': 'success', 'highscore': higher_lower_game_data['score']})

    except Exception as e:
        return jsonify({'result': 'error', 'details': 'Error fetching highscore', 'error' : str(e)})

@app.route('/insert_one', methods=['POST'])
def insert_one():
    data = request.get_json()
    name = data.get('name')
    spriteurl = data.get('spriteurl')
    try:
        # Insert the document into the collection
        result = collectionPokemon.insert_one({'name': name, 'spriteurl': spriteurl})

        # Return the result
        return jsonify({'result': 'success', 'details': str(result.inserted_id)})

    except Exception as e:
        # Handle errors gracefully
        return jsonify({'result': 'error', 'details': str(e)})

@app.route('/get_pokemon_starting_with/<input>', methods=['GET'])
def get_pokemon_starting_with(input):
    try:
        # Query the collection for Pokemon starting with the given input
        # Exclude the _id field
        results = collectionPokemon.find({'name': {'$regex': f'^{input}', '$options': 'i'}}, {'_id': 0})

        # Convert the results to a list of dictionaries
        pokemon_list = [pokemon for pokemon in results]

        # Return the results
        return jsonify(pokemon_list)

    except Exception as e:
        # Handle errors gracefully
        return jsonify({'result': 'error', 'details': str(e)})


@app.route('/saveHighscoreForMovesetGame', methods=['POST'])
def saveMovesetGameHighscoreToMongo():
    data = request.get_json()
    token = request.cookies.get('token')  # Get the token from the cookies
    username = extract_username(token)
    score = data.get('score')

    if username is None:
        return jsonify({'result': 'error', 'details': 'No user logged in'})

    try:
        # Create a filter to find the user
        user_filter = {'username': username}

        # Fetch the user document
        user_doc = collectionUsers.find_one(user_filter)

        # If the user document doesn't exist, return an error
        if user_doc is None:
            return jsonify({'result': 'error', 'details': 'User does not exist'})

        # If 'gamedata' doesn't exist, initialize it as an empty array
        if 'gamedata' not in user_doc:
            collectionUsers.update_one(user_filter, {"$set": {'gamedata': [{'game': 'movesetGame', 'score': score}]}})
            return jsonify({'result': 'success', 'score': score})

        # Find the index of the 'movesetGame' game data
        game_index = next((index for index, game in enumerate(user_doc['gamedata']) if game['game'] == 'movesetGame'), None)

        # If the 'movesetGame' game data doesn't exist, add it
        if game_index is None:
            collectionUsers.update_one(user_filter, {"$push": {'gamedata': {'game': 'movesetGame', 'score': score}}})
            return jsonify({'result': 'success', 'score': score})

        # If the new score is higher, update the score
        if user_doc['gamedata'][game_index]['score'] < score:
            collectionUsers.update_one(user_filter, {"$set": {f'gamedata.{game_index}.score': score}})
            return jsonify({'result': 'success', 'score': score})

        else:
            return jsonify({'result': 'success', 'details': 'Score is not higher than the current highscore'})

    except Exception as e:
        return jsonify({'result': 'error', 'details': 'Error saving highscore', 'error' : str(e)})
    

@app.route('/getHighscoreForMovesetGame', methods=['GET'])
def getHighscoreForMovesetGame():
    token = request.cookies.get('token')  # Get the token from the cookies
    username = extract_username(token)

    if username is None:
        return jsonify({'result': 'error', 'details': 'No user logged in'})

    try:
        # Create a filter to find the user
        user_filter = {'username': username}

        # Fetch the user document
        user_doc = collectionUsers.find_one(user_filter)

        # If the user document doesn't exist, return an error
        if user_doc is None:
            return jsonify({'result': 'error', 'details': 'User does not exist'})

        # Find the 'movesetGame' game data
        movesetGame_game_data = next((game for game in user_doc['gamedata'] if game['game'] == 'movesetGame'), None)

        # If the 'movesetGame' game data doesn't exist, return an error
        if movesetGame_game_data  is None:
            return jsonify({'result': 'error', 'details': 'No movesetGame game data'})

        # Return the highscore
        return jsonify({'result': 'success', 'highscore': movesetGame_game_data ['score']})

    except Exception as e:
        return jsonify({'result': 'error', 'details': 'Error fetching highscore', 'error' : str(e)})


@app.route('/')
def empty():
    return "Hello, PokeFun-Backend!"