#demo1233456787654356543456543543J



#hello hi

from pickletools import anyobject
from flask import Flask
from routes.upload import upload_bp
import serverless_wsgi ## for the lambda function
import json
import boto3
import os
import time
## testing comment for github desktop 
# add a new commetn 
##from routes.process import process_bp
from flask_cors import CORS
app = Flask(__name__)
app.register_blueprint(upload_bp)
CORS(app)
# test 2 for github desktop 
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

def calculate_all_time_metrics():
    """Calculate all-time metrics from database - SINGLE SOURCE OF TRUTH"""
    if not metrics_table:
        print("Metrics table not available")
        return None
    
    try:
        print("Starting metrics calculation...")
        # Get ALL metrics ever processed
        all_metrics_response = metrics_table.scan()
        all_metrics = all_metrics_response.get('Items', [])
        print(f"Found {len(all_metrics)} metrics in database")
        
        # Calculate all-time dashboard metrics
        total_all_time = len(all_metrics)
        
        if all_metrics:
            avg_latency = sum(int(m.get('latency', 0)) for m in all_metrics) / len(all_metrics)
            avg_accuracy = sum(float(m.get('accuracy', 0)) for m in all_metrics) / len(all_metrics)
        else:
            print("No existing metrics found, using defaults")
            avg_latency = 0
            avg_accuracy = 0
        
        aggregated_metrics = {
            'total': total_all_time,
            'avgLatency': round(avg_latency),
            'avgAccuracy': round(avg_accuracy, 1),
            'throughput': total_all_time,  # Simple throughput = total count
            'timestamp': int(time.time() * 1000)
        }
        
        print(f"Calculated metrics: {total_all_time} total, {avg_latency:.0f}ms avg latency, {avg_accuracy:.1f}% avg accuracy")
        return aggregated_metrics
        
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        import traceback
        traceback.print_exc()
        return None


def broadcast_metrics_to_all():
    """Broadcast current metrics to all connected WebSocket clients"""
    if not connections_table:
        print("Tables not available for broadcasting")
        return
    
    try:
        print("Starting broadcast_metrics_to_all...")
        # Get current metrics
        metrics = calculate_all_time_metrics()
        if not metrics:
            print("No metrics to broadcast - calculate_all_time_metrics returned None")
            return
        
        print(f"Broadcasting metrics: {metrics}")
        
        # Get all active connections
        connections_response = connections_table.scan()
        connections = connections_response.get('Items', [])
        
        if not connections:
            print("No active connections to broadcast to")
            return
        
        # Get WebSocket endpoint
        ws_endpoint = os.environ.get('WS_ENDPOINT')
        if not ws_endpoint:
            print("WebSocket endpoint not configured")
            return
        
        # Broadcast to all connections
        apigateway = boto3.client('apigatewaymanagementapi', 
                                endpoint_url=ws_endpoint.replace('wss://', 'https://'))
        
        message = json.dumps({
            'type': 'metrics-update',
            'data': metrics
        })
        
        successful_broadcasts = 0
        for connection in connections:
            try:
                apigateway.post_to_connection(
                    ConnectionId=connection['connectionId'],
                    Data=message
                )
                successful_broadcasts += 1
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
        
        print(f"Broadcasted metrics to {successful_broadcasts}/{len(connections)} connections")
        
    except Exception as e:
        print(f"Error broadcasting metrics: {e}")

def handle_websocket_connect(connection_id):
    """Handle WebSocket connection"""
    if not connections_table:
        print("Connections table not available")
        return {"statusCode": 500}
    
    try:
        # Store the connection
        connections_table.put_item(
            Item={
                'connectionId': connection_id,
                'timestamp': int(time.time() * 1000),
                'connectedAt': time.strftime('%Y-%m-%d %H:%M:%S UTC')
            }
        )
        print(f"Connection {connection_id} stored successfully - waiting for metrics request")
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
        elif route_key == '$default':
            # Handle incoming messages
            try:
                body = event.get('body', '{}')
                message = json.loads(body) if body else {}
                action = message.get('action')
                
                print(f"Received WebSocket message: action='{action}' from {connection_id}")
                
                if action == 'get-metrics':
                    # Send current metrics using the same function that works after image processing
                    broadcast_metrics_to_all()
                    return {"statusCode": 200}
                else:
                    print(f"Unknown action: {action}")
                    return {"statusCode": 200}
                    
            except Exception as e:
                print(f"Error handling WebSocket message: {e}")
                return {"statusCode": 500}
        else:
            return {"statusCode": 200}
    
    # Handle regular HTTP requests through Flask
    return serverless_wsgi.handle_request(app, event, context)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=True)





# demo for github desktop 