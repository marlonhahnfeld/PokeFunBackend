from mongo import app
from mongo import CORS

if __name__ == '__main__':
    CORS(app, resources={r"/*": {"origins": "https://poke-fun-blush.vercel.app/"}}, supports_credentials=True)
    app.run(debug=True)