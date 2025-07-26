from pickletools import anyobject
from flask import Flask
from routes.upload import upload_bp
import serverless_wsgi ## for the lambda function
import json
import boto3
import os
import time

##from routes.process import process_bp
from flask_cors import CORS
app = Flask(__name__)
app.register_blueprint(upload_bp)
##app.register_blueprint(process_bp)

# Initialize DynamoDB client for WebSocket functionality
try:
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    connections_table = dynamodb.Table('WSConnections')
    metrics_table = dynamodb.Table('InvoiceMetrics')
    print("DynamoDB connected successfully")
except Exception as e:
    print(f"DynamoDB connection failed: {e}")
    dynamodb = None
    connections_table = None
    metrics_table = None

# ADD THIS HEALTH CHECK ENDPOINT
@app.route('/health', methods=['GET'])
def health_check():
    return {"status": "healthy"}, 200

CORS(app, origins = ["*"])

def handle_websocket_connect(connection_id):
    """Handle WebSocket connection"""
    if not connections_table:
        print("Connections table not available")
        return {"statusCode": 500}
    
    try:
        connections_table.put_item(
            Item={
                'connectionId': connection_id,
                'timestamp': int(time.time() * 1000),
                'connectedAt': time.strftime('%Y-%m-%d %H:%M:%S UTC')
            }
        )
        print(f"Connection {connection_id} stored successfully")
        return {"statusCode": 200}
    except Exception as e:
        print(f"Error storing connection: {e}")
        return {"statusCode": 500}

def handle_websocket_disconnect(connection_id):
    """Handle WebSocket disconnection"""
    if not connections_table:
        print("Connections table not available")
        return {"statusCode": 500}
    
    try:
        connections_table.delete_item(
            Key={'connectionId': connection_id}
        )
        print(f"Connection {connection_id} removed successfully")
        return {"statusCode": 200}
    except Exception as e:
        print(f"Error removing connection: {e}")
        return {"statusCode": 500}

def broadcast_metrics():
    """Calculate and broadcast metrics to all connected clients"""
    if not connections_table or not metrics_table:
        print("Tables not available for broadcasting")
        return
    
    try:
        # Get metrics from last 60 seconds
        now = int(time.time() * 1000)
        sixty_seconds_ago = now - 60000
        
        response = metrics_table.scan(
            FilterExpression='#ts >= :start',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':start': sixty_seconds_ago}
        )
        
        metrics = response.get('Items', [])
        
        # Calculate aggregated metrics
        total = len(metrics)
        avg_latency = sum(int(m.get('latency', 0)) for m in metrics) / max(total, 1)
        avg_accuracy = sum(float(m.get('accuracy', 0)) for m in metrics) / max(total, 1)
        throughput = total / 60  # per second
        
        aggregated_metrics = {
            'total': total,
            'avgLatency': round(avg_latency),
            'avgAccuracy': round(avg_accuracy, 1),
            'throughput': round(throughput, 2),
            'timestamp': now
        }
        
        # Get all active connections
        connections_response = connections_table.scan()
        connections = connections_response.get('Items', [])
        
        if not connections:
            print("No active connections to broadcast to")
            return
        
        # Broadcast to all connections
        ws_endpoint = os.environ.get('WS_ENDPOINT')
        if not ws_endpoint:
            print("WebSocket endpoint not configured")
            return
        
        apigateway = boto3.client('apigatewaymanagementapi', 
                                endpoint_url=ws_endpoint.replace('wss://', 'https://'))
        
        message = json.dumps({
            'type': 'metrics-update',
            'data': aggregated_metrics
        })
        
        for connection in connections:
            try:
                apigateway.post_to_connection(
                    ConnectionId=connection['connectionId'],
                    Data=message
                )
                print(f"Sent metrics to connection {connection['connectionId']}")
            except Exception as e:
                print(f"Error sending to {connection['connectionId']}: {e}")
                # Remove stale connection
                if 'GoneException' in str(e) or '410' in str(e):
                    try:
                        connections_table.delete_item(
                            Key={'connectionId': connection['connectionId']}
                        )
                        print(f"Removed stale connection {connection['connectionId']}")
                    except:
                        pass
        
        print(f"Broadcasted metrics to {len(connections)} connections")
        
    except Exception as e:
        print(f"Error broadcasting metrics: {e}")

def lambda_handler(event, context):
    """Handle both HTTP and WebSocket events"""
    
    # Check if this is a WebSocket event
    if 'requestContext' in event and 'routeKey' in event['requestContext']:
        route_key = event['requestContext']['routeKey']
        connection_id = event['requestContext']['connectionId']
        
        print(f"WebSocket event: {route_key}, connection: {connection_id}")
        
        if route_key == '$connect':
            return handle_websocket_connect(connection_id)
        elif route_key == '$disconnect':
            return handle_websocket_disconnect(connection_id)
        else:
            return {"statusCode": 200}
    
    # Handle regular HTTP requests through Flask
    return serverless_wsgi.handle_request(app, event, context)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=True)





