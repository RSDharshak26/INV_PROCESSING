# 🚀 Floating WebSocket Dashboard Implementation

This README documents all code changes made to implement a real-time floating dashboard widget that appears on every page of the invoice processing application.

## 📋 Overview of Changes

**Files Modified:**
- `main_app/backend/app.py` - Added WebSocket handling to existing Lambda
- `main_app/backend/routes/upload.py` - Added metrics collection and broadcasting
- `main_app/backend/template.yaml` - Added DynamoDB permissions and environment variables
- `main_app/frontend/components/FloatingDashboard.tsx` - New floating widget component
- `main_app/frontend/app/layout.tsx` - Added widget to global layout
- `main_app/infra/infra.yml` - Added WebSocket API and DynamoDB tables

---

## 🐍 Backend Changes (Python/Flask/Lambda)

### 1. Modified `main_app/backend/app.py`

#### **Added WebSocket Event Handling**

```python
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
```

**🎓 Learning Points:**
- **Event Detection:** WebSocket events have `requestContext.routeKey` (like `$connect`, `$disconnect`)
- **Dual Handling:** Same Lambda function handles both HTTP (Flask) and WebSocket events
- **Route Keys:** `$connect` and `$disconnect` are AWS API Gateway V2 special routes
- **Fallback Pattern:** If not WebSocket, pass to existing Flask handler

#### **Added DynamoDB Connection Management**

```python
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
```

**🎓 Learning Points:**
- **Graceful Degradation:** If DynamoDB fails, variables set to `None` instead of crashing
- **boto3.resource vs client:** `resource()` provides higher-level, object-oriented interface
- **Global Variables:** Tables initialized once at Lambda cold start, reused across invocations
- **Error Handling:** Try-catch prevents Lambda from failing during initialization

#### **WebSocket Connection Handlers**

```python
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
```

**🎓 Learning Points:**
- **Guard Clauses:** Check if table available before proceeding
- **DynamoDB put_item:** Creates new item or overwrites existing one
- **Timestamp Formats:** `time.time() * 1000` for milliseconds since epoch
- **Return Format:** WebSocket Lambda must return `{"statusCode": number}` format
- **Connection ID:** Unique identifier provided by API Gateway for each WebSocket connection

### 2. Modified `main_app/backend/routes/upload.py`

#### **Added Metrics Collection**

```python
import uuid
import boto3
import json

# Initialize DynamoDB for metrics
try:
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    metrics_table = dynamodb.Table('InvoiceMetrics')
    connections_table = dynamodb.Table('WSConnections')
    print("DynamoDB metrics tables connected successfully")
except Exception as e:
    print(f"DynamoDB metrics connection failed: {e}")
    dynamodb = None
    metrics_table = None
    connections_table = None
```

**🎓 Learning Points:**
- **Module-Level Initialization:** DynamoDB clients created when module imports, not per request
- **Import Strategy:** Add new imports at top, group related imports together
- **Separate Initialization:** Each module can have its own DynamoDB connection

#### **Metrics Storage Function**

```python
def store_metrics(invoice_id, processing_time_ms, accuracy_score=95):
    """Store processing metrics in DynamoDB for dashboard"""
    if not metrics_table:
        print("Metrics table not available, skipping metrics storage")
        return
    
    try:
        metrics_table.put_item(
            Item={
                'invoiceId': invoice_id,
                'timestamp': int(time.time() * 1000),  # milliseconds since epoch
                'latency': processing_time_ms,
                'accuracy': accuracy_score,
                'processedAt': time.strftime('%Y-%m-%d %H:%M:%S UTC')
            }
        )
        print(f"Stored metrics for invoice {invoice_id}: {processing_time_ms}ms, {accuracy_score}%")
    except Exception as e:
        print(f"Error storing metrics: {e}")
```

**🎓 Learning Points:**
- **Function Parameters:** Mix of required (`invoice_id`, `processing_time_ms`) and optional (`accuracy_score=95`)
- **Data Types:** Store both numbers (`timestamp`, `latency`) and strings (`invoiceId`, `processedAt`)
- **Error Isolation:** Function fails gracefully - doesn't break main upload flow if metrics fail
- **Logging Strategy:** Print both success and failure cases for debugging

#### **Accuracy Calculation**

```python
def calculate_accuracy_score(detected_text):
    """Calculate accuracy score based on detected text quality"""
    if not detected_text:
        return 0
    
    # Simple heuristic: longer text with common invoice keywords = higher accuracy
    text_lower = detected_text.lower()
    invoice_keywords = ['invoice', 'total', 'amount', 'date', 'tax', 'subtotal', '$']
    keyword_count = sum(1 for keyword in invoice_keywords if keyword in text_lower)
    
    # Base score on text length and keyword presence
    length_score = min(len(detected_text) / 1000 * 50, 50)  # Up to 50% for text length
    keyword_score = (keyword_count / len(invoice_keywords)) * 50  # Up to 50% for keywords
    
    total_score = length_score + keyword_score
    return min(int(total_score), 95)  # Cap at 95%
```

**🎓 Learning Points:**
- **Heuristic Algorithm:** Simple rule-based approach for scoring accuracy
- **List Comprehension:** `sum(1 for keyword in invoice_keywords if keyword in text_lower)`
- **Mathematical Capping:** `min()` function prevents scores from exceeding limits
- **Type Conversion:** `int(total_score)` converts float to integer for storage

#### **Real-time Broadcasting**

```python
def broadcast_metrics_update():
    """Broadcast updated metrics to all connected WebSocket clients"""
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
```

**🎓 Learning Points:**
- **DynamoDB FilterExpression:** Uses attribute names (`#ts`) and values (`:start`) for reserved words
- **Time Calculations:** `now - 60000` for 60 seconds ago (milliseconds)
- **Safe Division:** `max(total, 1)` prevents division by zero
- **Data Aggregation:** Multiple reduce operations (`sum()`, `len()`) for statistical calculations
- **Precision Control:** `round(value, decimal_places)` for display formatting

#### **Integration with Upload Flow**

```python
@upload_bp.route('/receive', methods=['GET','POST','OPTIONS'])
def receive_image():
    try:
        # Start timing for metrics
        start_time = time.time()
        
        # ... existing file processing code ...
        
        # Process the uploaded file
        detected_text, text_segments, output_filename = detect_text(temp_path)
        
        # Calculate processing time and accuracy for metrics
        processing_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        accuracy_score = calculate_accuracy_score(detected_text)
        
        # Generate unique invoice ID and store metrics
        invoice_id = f"inv_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        store_metrics(invoice_id, processing_time, accuracy_score)
        
        # Broadcast updated metrics to connected dashboards
        broadcast_metrics_update()
```

**🎓 Learning Points:**
- **Timing Pattern:** `start_time = time.time()` before, calculate difference after
- **UUID Generation:** `uuid.uuid4().hex[:8]` creates short unique identifier
- **Time Conversion:** `(time.time() - start_time) * 1000` converts seconds to milliseconds
- **Non-blocking Integration:** Metrics code doesn't affect main upload functionality
- **Function Composition:** Chain function calls (`store_metrics` → `broadcast_metrics_update`)

---

## ⚛️ Frontend Changes (React/TypeScript/Next.js)

### 1. Created `main_app/frontend/components/FloatingDashboard.tsx`

#### **TypeScript Interface Definition**

```typescript
interface Metrics {
  total: number;
  throughput: number;
  avgLatency: number;
  avgAccuracy: number;
  timestamp: number;
}
```

**🎓 Learning Points:**
- **Interface vs Type:** `interface` is preferred for object shapes in TypeScript
- **Property Types:** All properties are `number` type - matches backend data structure
- **Naming Convention:** camelCase for properties (JavaScript convention)

#### **Component State Management**

```typescript
const [metrics, setMetrics] = useState<Metrics | null>(null);
const [isMinimized, setIsMinimized] = useState(false);
const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('connecting');
const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
```

**🎓 Learning Points:**
- **Generic useState:** `useState<Type>()` provides type safety for state
- **Union Types:** `'connecting' | 'connected' | 'disconnected' | 'error'` limits possible values
- **Nullable Types:** `Metrics | null` and `Date | null` handle cases when data isn't available
- **Default Values:** Initial states provided for all state variables

#### **WebSocket Connection Logic**

```typescript
useEffect(() => {
  const wsEndpoint = process.env.NEXT_PUBLIC_WS_ENDPOINT || 'wss://your-websocket-api.execute-api.us-east-1.amazonaws.com/dev';
  
  const connectWebSocket = () => {
    console.log('Connecting to WebSocket:', wsEndpoint);
    const ws = new WebSocket(wsEndpoint);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnectionStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('Received message:', message);
        
        if (message.type === 'metrics-update') {
          setMetrics(message.data);
          setLastUpdate(new Date());
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event);
      setConnectionStatus('disconnected');
      
      // Attempt to reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000);
    };

    return ws;
  };

  const websocket = connectWebSocket();

  return () => {
    websocket.close();
  };
}, []);
```

**🎓 Learning Points:**
- **useEffect Dependency Array:** Empty array `[]` means effect runs once on mount
- **Environment Variables:** `process.env.NEXT_PUBLIC_*` accessible in browser (Next.js convention)
- **WebSocket Event Handlers:** `onopen`, `onmessage`, `onclose` are standard WebSocket API
- **JSON Parsing:** Always wrap `JSON.parse()` in try-catch for malformed data
- **Reconnection Pattern:** `setTimeout(connectWebSocket, 3000)` for automatic retry
- **Cleanup Function:** `return () => websocket.close()` prevents memory leaks
- **Closure Pattern:** Inner function `connectWebSocket` can access outer variables

#### **Conditional Rendering Patterns**

```typescript
{connectionStatus === 'connected' && metrics ? (
  <div className="grid grid-cols-2 gap-2 text-xs">
    <div className="bg-blue-50 p-2 rounded">
      <div className="text-blue-600 font-medium">Total</div>
      <div className="text-blue-800 font-bold">{metrics.total}</div>
    </div>
    {/* ... more metric cards ... */}
  </div>
) : (
  <div className="text-center py-4">
    {connectionStatus === 'connecting' && (
      <div className="text-gray-500 text-sm">
        <div className="animate-pulse">Connecting...</div>
      </div>
    )}
    {connectionStatus === 'connected' && !metrics && (
      <div className="text-gray-500 text-sm">
        <div>Waiting for data...</div>
        <div className="text-xs mt-1">Process some invoices to see metrics</div>
      </div>
    )}
  </div>
)}
```

**🎓 Learning Points:**
- **Logical AND:** `condition && <JSX>` renders JSX only if condition is true
- **Ternary Operator:** `condition ? <TrueJSX> : <FalseJSX>` for if-else rendering
- **Multiple Conditions:** Chain conditions with `&&` for complex logic
- **Falsy Values:** Both `null` and `false` are falsy, so `!metrics` checks for no data
- **CSS Classes:** Tailwind utility classes for styling (`grid-cols-2`, `bg-blue-50`, etc.)

#### **Event Handler Functions**

```typescript
const formatValue = (val: number) => {
  if (val === 0) return '0';
  if (val < 1) return val.toFixed(2);
  if (val < 100) return val.toFixed(1);
  return Math.round(val).toString();
};

const getStatusColor = () => {
  switch (connectionStatus) {
    case 'connected': return 'text-green-500';
    case 'connecting': return 'text-yellow-500';
    case 'disconnected': return 'text-red-500';
    case 'error': return 'text-red-500';
    default: return 'text-gray-500';
  }
};
```

**🎓 Learning Points:**
- **Function Type Annotations:** `(val: number)` specifies parameter type
- **Early Returns:** Multiple `if` statements with early returns for clarity
- **Number Methods:** `toFixed(2)` for decimal places, `Math.round()` for integers
- **Switch Statements:** Better than if-else chains for multiple discrete values
- **Default Case:** Always include `default` case in switch statements

### 2. Modified `main_app/frontend/app/layout.tsx`

#### **Component Import and Usage**

```typescript
import '../styles/globals.css';
import FloatingDashboard from '../components/FloatingDashboard';

export const metadata = {
  title: 'Invoice Processing App',
  description: 'AI-powered invoice processing with real-time dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {children}
        <FloatingDashboard />
      </body>
    </html>
  )
}
```

**🎓 Learning Points:**
- **Relative Imports:** `../` navigates up directory levels
- **Default Exports:** `FloatingDashboard` imported without curly braces
- **Metadata Export:** Next.js 13+ uses exported `metadata` object for page metadata
- **Type Annotations:** `{ children: React.ReactNode }` types the props parameter
- **Component Placement:** `<FloatingDashboard />` after `{children}` renders on top (CSS z-index)
- **Layout Pattern:** `layout.tsx` wraps all pages in the directory

---

## 🏗️ Infrastructure Changes (AWS CloudFormation)

### Overview of Resources Added

**Big Picture:** Added minimal infrastructure to enable real-time communication between browser and backend, using existing Lambda function for all logic.

**Key Resources:**
1. **2 DynamoDB Tables** - Store connection IDs and metrics data
2. **1 WebSocket API** - Handle real-time browser connections  
3. **WebSocket Routes & Integrations** - Route WebSocket events to existing Lambda
4. **Permissions** - Allow WebSocket API to invoke Lambda function

### 1. Modified `main_app/backend/template.yaml`

#### **Added Environment Variables and Permissions**

```yaml
Environment:
  Variables:
    GOOGLE_APPLICATION_CREDENTIALS: ./inv-processing-authentication-f9e50adadbc5.json
    WS_ENDPOINT: !Sub "wss://${WebSocketApi}.execute-api.${AWS::Region}.amazonaws.com/dev"
Policies:
  - DynamoDBCrudPolicy:
      TableName: WSConnections
  - DynamoDBCrudPolicy:
      TableName: InvoiceMetrics
  - Statement:
      Effect: Allow
      Action:
        - execute-api:ManageConnections
      Resource: !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:*/*"
```

**🎓 Learning Points:**
- **CloudFormation Functions:** `!Sub` substitutes variables in strings
- **SAM Policies:** `DynamoDBCrudPolicy` is a SAM-specific managed policy
- **Environment Variables:** Available in Lambda as `os.environ.get('WS_ENDPOINT')`
- **ARN Patterns:** `arn:aws:service:region:account:resource` is standard AWS format
- **IAM Actions:** `execute-api:ManageConnections` allows posting to WebSocket connections

### 2. Modified `main_app/infra/infra.yml`

#### **DynamoDB Tables**

```yaml
WSConnectionsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: WSConnections
    AttributeDefinitions:
      - AttributeName: connectionId
        AttributeType: S
    KeySchema:
      - AttributeName: connectionId
        KeyType: HASH
    BillingMode: PAY_PER_REQUEST

InvoiceMetricsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: InvoiceMetrics
    AttributeDefinitions:
      - AttributeName: invoiceId
        AttributeType: S
      - AttributeName: timestamp
        AttributeType: N
    KeySchema:
      - AttributeName: invoiceId
        KeyType: HASH
      - AttributeName: timestamp
        KeyType: RANGE
    BillingMode: PAY_PER_REQUEST
```

**🎓 Learning Points:**
- **DynamoDB Key Types:** `HASH` (partition key) distributes data, `RANGE` (sort key) orders within partition
- **Attribute Types:** `S` = String, `N` = Number in DynamoDB
- **Billing Modes:** `PAY_PER_REQUEST` charges per operation, `PROVISIONED` charges for reserved capacity
- **Composite Keys:** Using both HASH and RANGE allows multiple items per partition
- **Table Naming:** Hardcoded names vs parameterized - hardcoded simpler for single environment

#### **WebSocket API Gateway V2**

```yaml
WebSocketApi:
  Type: AWS::ApiGatewayV2::Api
  Properties:
    Name: InvoiceDashboardWS
    ProtocolType: WEBSOCKET
    RouteSelectionExpression: $request.body.action

ConnectRoute:
  Type: AWS::ApiGatewayV2::Route
  Properties:
    ApiId: !Ref WebSocketApi
    RouteKey: $connect
    AuthorizationType: NONE
    OperationName: ConnectRoute
    Target: !Sub integrations/${ConnectInteg}
```

**🎓 Learning Points:**
- **API Gateway V2:** Supports WebSocket protocol (V1 only supports HTTP)
- **Route Selection:** `$request.body.action` field determines which route to use
- **Special Routes:** `$connect` and `$disconnect` are built-in WebSocket lifecycle routes
- **Resource References:** `!Ref WebSocketApi` gets the resource ID
- **Target Format:** `integrations/IntegrationId` is required format for route targets

#### **Lambda Integrations**

```yaml
ConnectInteg:
  Type: AWS::ApiGatewayV2::Integration
  Properties:
    ApiId: !Ref WebSocketApi
    Description: Connect Integration
    IntegrationType: AWS_PROXY
    IntegrationUri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:sam-app-UploadFunction-*/invocations
```

**🎓 Learning Points:**
- **AWS_PROXY Integration:** Passes entire request to Lambda, expects specific response format
- **Lambda ARN Pattern:** Complex ARN structure includes API Gateway service endpoint
- **Wildcard Matching:** `*` in function name matches SAM-generated suffixes
- **API Gateway to Lambda:** Two-step process: Route → Integration → Lambda function

## 🎯 Key Learning Takeaways

### **Python/Backend Patterns:**
1. **Graceful Degradation:** Always check if resources are available before using
2. **Event-Driven Architecture:** Single Lambda handles multiple event types
3. **Timing Measurements:** Use `time.time()` before/after for performance metrics
4. **Error Isolation:** Don't let optional features break core functionality

### **React/Frontend Patterns:**
1. **Type Safety:** Use TypeScript interfaces for data structures
2. **State Management:** Multiple `useState` hooks for different concerns
3. **Effect Cleanup:** Always clean up resources in `useEffect` return function
4. **Conditional Rendering:** Use `&&` and `?:` operators for UI state management

### **Infrastructure Patterns:**
1. **Resource Relationships:** Use `!Ref` to link resources together
2. **Minimal Permissions:** Grant only specific actions needed
3. **Environment Variables:** Pass configuration through Lambda environment
4. **Service Integration:** Connect services through ARNs and policies

This implementation demonstrates how to add real-time features to existing applications with minimal changes, using AWS managed services for scalability and reliability.
