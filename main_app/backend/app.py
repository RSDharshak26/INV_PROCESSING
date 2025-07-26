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

def calculate_current_metrics():
    """Calculate current all-time metrics from database"""
    if not metrics_table:
        return None
    
    try:
        # Get ALL metrics ever processed (no time filter)
        all_metrics_response = metrics_table.scan()
        all_metrics = all_metrics_response.get('Items', [])
        
        # Calculate all-time dashboard metrics
        total_all_time = len(all_metrics)  # Total invoices ever processed
        
        # Calculate all-time averages
        if all_metrics:
            avg_latency = sum(int(m.get('latency', 0)) for m in all_metrics) / len(all_metrics)
            avg_accuracy = sum(float(m.get('accuracy', 0)) for m in all_metrics) / len(all_metrics)
        else:
            avg_latency = 0
            avg_accuracy = 0
        
        # Simple throughput: total processed
        throughput = total_all_time
        
        aggregated_metrics = {
            'total': total_all_time,        # All-time total
            'avgLatency': round(avg_latency),   # All-time average latency
            'avgAccuracy': round(avg_accuracy, 1),  # All-time average accuracy
            'throughput': throughput,       # Just total count
            'timestamp': int(time.time() * 1000)
        }
        
        print(f"Current metrics: {total_all_time} total, {avg_latency:.0f}ms avg latency, {avg_accuracy:.1f}% avg accuracy")
        return aggregated_metrics
        
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return None

def send_current_metrics_to_new_connection(connection_id):
    """Send current metrics to a newly connected client"""
    if not connections_table or not metrics_table:
        print("Tables not available for sending metrics")
        return
    
    try:
        # Use the SAME logic as the working upload route
        # Get ALL metrics ever processed (no time filter)
        all_metrics_response = metrics_table.scan()
        all_metrics = all_metrics_response.get('Items', [])
        
        # Calculate all-time dashboard metrics (SAME as upload route)
        total_all_time = len(all_metrics)  # Total invoices ever processed
        
        # Calculate all-time averages
        if all_metrics:
            avg_latency = sum(int(m.get('latency', 0)) for m in all_metrics) / len(all_metrics)
            avg_accuracy = sum(float(m.get('accuracy', 0)) for m in all_metrics) / len(all_metrics)
        else:
            avg_latency = 0
            avg_accuracy = 0
        
        # Simple throughput: total processed
        throughput = total_all_time
        
        aggregated_metrics = {
            'total': total_all_time,        # All-time total
            'avgLatency': round(avg_latency),   # All-time average latency
            'avgAccuracy': round(avg_accuracy, 1),  # All-time average accuracy
            'throughput': throughput,       # Just total count
            'timestamp': int(time.time() * 1000)
        }
        
        print(f"Sending initial metrics to {connection_id}: {total_all_time} total, {avg_latency:.0f}ms avg latency, {avg_accuracy:.1f}% avg accuracy")
        
        # Send to this specific connection
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
        
        apigateway.post_to_connection(
            ConnectionId=connection_id,
            Data=message
        )
        print(f"Successfully sent initial metrics to connection {connection_id}")
        
    except Exception as e:
        print(f"Error sending initial metrics to {connection_id}: {e}")

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
        print(f"Connection {connection_id} stored successfully")
        
        # Don't send metrics immediately - wait for frontend to request them
        
        return {"statusCode": 200}
    except Exception as e:
        print(f"Error storing connection: {e}")
        return {"statusCode": 500}

def handle_websocket_message(connection_id, message):
    """Handle WebSocket messages from frontend"""
    try:
        data = json.loads(message)
        action = data.get('action')
        
        print(f"Received action '{action}' from {connection_id}")
        
        if action == 'get-metrics':
            # Send current metrics when requested
            send_current_metrics_to_new_connection(connection_id)
        
        return {"statusCode": 200}
    except Exception as e:
        print(f"Error handling message from {connection_id}: {e}")
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
        # Use the SAME logic as upload route - just send to ALL connections
        # Get ALL metrics ever processed (no time filter)
        all_metrics_response = metrics_table.scan()
        all_metrics = all_metrics_response.get('Items', [])
        
        # Calculate all-time dashboard metrics (SAME as upload route)
        total_all_time = len(all_metrics)
        
        if all_metrics:
            avg_latency = sum(int(m.get('latency', 0)) for m in all_metrics) / len(all_metrics)
            avg_accuracy = sum(float(m.get('accuracy', 0)) for m in all_metrics) / len(all_metrics)
        else:
            avg_latency = 0
            avg_accuracy = 0
        
        aggregated_metrics = {
            'total': total_all_time,
            'avgLatency': round(avg_latency),
            'avgAccuracy': round(avg_accuracy, 1),
            'throughput': total_all_time,
            'timestamp': int(time.time() * 1000)
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
        elif route_key == '$default':
            # Handle messages sent from frontend
            message = event.get('body', '{}')
            return handle_websocket_message(connection_id, message)
        else:
            return {"statusCode": 200}
    
    # Handle regular HTTP requests through Flask
    return serverless_wsgi.handle_request(app, event, context)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=True)





