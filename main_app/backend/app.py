from flask import Flask
from routes.upload import upload_bp
##from routes.process import process_bp
from flask_cors import CORS
app = Flask(__name__)
app.register_blueprint(upload_bp)
##app.register_blueprint(process_bp)


CORS(app, origins=["http://localhost:3000"])
if __name__ == "__main__":
    app.run(debug=True)
