from pickletools import anyobject
from flask import Flask
from routes.upload import upload_bp


import serverless_wsgi ## for the lambda function

##from routes.process import process_bp
from flask_cors import CORS
app = Flask(__name__)
app.register_blueprint(upload_bp)
##app.register_blueprint(process_bp)




# ADD THIS HEALTH CHECK ENDPOINT
@app.route('/health', methods=['GET'])
def health_check():
    return {"status": "healthy"}, 200


CORS(app, origins = ["*"])

def lambda_handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=True)





