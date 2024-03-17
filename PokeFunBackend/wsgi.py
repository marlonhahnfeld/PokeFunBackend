from PokeFunBackend.mongo import app
from PokeFunBackend.mongo import CORS

if __name__ == '__main__':
    CORS(app, supports_credentials=True)  
    app.run(debug=True)