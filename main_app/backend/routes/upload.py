from flask import Blueprint, request
from PIL import Image, ImageDraw
from dotenv import load_dotenv
load_dotenv()
import time
import re
import uuid
import boto3
import json
from botocore.exceptions import ClientError

upload_bp = Blueprint('upload', __name__)

def get_secret():
    secret_name = "google_ocr"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

def store_metrics(invoice_id, processing_time_ms, accuracy_score=95):
    """Store processing metrics in DynamoDB for dashboard"""
    # Import here to avoid circular imports
    from app import metrics_table
    
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


def detect_text(path):
    """Detects text in the file."""
    from google.cloud import vision
    from google.oauth2 import service_account

    # Get credentials from AWS Secrets Manager
    credentials_info = get_secret()
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    client = vision.ImageAnnotatorClient(credentials=credentials)

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.annotate_image({
        'image': image,
        'features': [{'type_': vision.Feature.Type.TEXT_DETECTION}]
    })
    texts = response.text_annotations ## 0th index has the whole text detection as a string 
    ##print("Texts:")
    
    
    
    # Get the complete text from the first annotation (index 0)
    detected_text = texts[0].description if texts else ""
    
    # Extract individual text segments with bounding boxes
    text_segments = []
    for text in texts[1:]:  # Skip first one (full text), process individual words
        vertices = text.bounding_poly.vertices
        bounding_box = {
            "x1": vertices[0].x, "y1": vertices[0].y,  # Top-left
            "x2": vertices[1].x, "y2": vertices[1].y,  # Top-right
            "x3": vertices[2].x, "y3": vertices[2].y,  # Bottom-right
            "x4": vertices[3].x, "y4": vertices[3].y   # Bottom-left
        }
        text_segments.append({
            "text": text.description,
            "bounding_box": bounding_box
        })
    
    #regex for pattern matching 
    pattern = r'\d+\.?\d+'  # this matches all digits
    matches = re.findall(pattern, detected_text)  # returns list of all matches
    print("the matches are : ",matches)
    
    
    # Print bounding boxes for debugging (optional)
    for text in texts[1:]:  # Skip first one, process individual words for bounding boxes
        vertices = [
            f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices
        ]
        print("bounds: {}".format(",".join(vertices)))
    
    # Draw boxes on the image and save it
    output_filename = f"output_with_boxes_{int(time.time())}.jpg"
    draw_boxes_on_image(path, texts, output_filename)
    
    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )
    
    return detected_text, text_segments, output_filename



def draw_boxes_on_image(image_path, texts, output_filename):
    try:
        # Try multiple PIL opening methods
        image = None
        
        # Method 1: Standard open
        try:
            image = Image.open(image_path)
            print("PIL Method 1 (standard) succeeded")
        except:
            print("PIL Method 1 failed, trying method 2")
            
            # Method 2: Force specific format
            try:
                with open(image_path, 'rb') as f:
                    image = Image.open(f)
                    image = image.convert('RGB')  # Force RGB mode
                print("PIL Method 2 (RGB convert) succeeded")
            except:
                print("PIL Method 2 failed, trying method 3")
                
                # Method 3: Read raw bytes and recreate
                try:
                    import io
                    with open(image_path, 'rb') as f:
                        img_bytes = f.read()
                    image = Image.open(io.BytesIO(img_bytes))
                    image = image.convert('RGB')
                    print("PIL Method 3 (BytesIO) succeeded")
                except Exception as e:
                    print(f"All PIL methods failed: {e}")
                    raise
        
        if image is None:
            raise Exception("Could not open image with any method")
            
        # Draw bounding boxes
        draw = ImageDraw.Draw(image)
        for text in texts:
            vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
            if len(vertices) == 4:
                draw.line(vertices + [vertices[0]], width=2, fill='red')
        
        # Save the image with boxes in tmp directory for Lambda
        output_path = f"/tmp/{output_filename}"
        image.save(output_path, 'JPEG', quality=95)  # Force JPEG format
        print(f"Image saved to: {output_path}")
        
    except Exception as e:
        print(f"draw_boxes_on_image error: {e}")
        raise

##pip install flask-cors. this is to let 2 ports to talk to each other 



def post_process(text_segments):
    #this is where we will do the post processing of the detected text
    #we will use the detected text to extract the data we need
    #we will return the data we need
    
    word_names = ["Price","Quantity","Total"]
    headers = []
    
    # Find header elements
    for element in text_segments:
        if element["text"] in word_names:
            headers.append(element)
    
    # Find column-aligned elements for each header
    columns = {}
    for header in headers:
        column_name = header["text"]
        columns[column_name] = [header]
        
        header_x1 = header["bounding_box"]["x1"]
        header_x2 = header["bounding_box"]["x2"]
        
        # Find other elements that align with this header column
        for element in text_segments:
            if element == header:
                continue
                
            elem_x1 = element["bounding_box"]["x1"]
            elem_x2 = element["bounding_box"]["x2"]
            
            # Check if element aligns with header (overlap in x-range)
            if (elem_x1 <= header_x2 and elem_x2 >= header_x1):
                columns[column_name].append(element)
    
    return columns if columns else headers

@upload_bp.route('/receive', methods=['GET','POST','OPTIONS'])
def receive_image():
    
    
    # Handle CORS preflight request - ADD THIS BLOCK
    if request.method == 'OPTIONS':
        from flask import make_response
        resp = make_response('')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp
    
    try:
        print("Request received")
        
        # Start timing for metrics
        start_time = time.time()
        
        if 'file' not in request.files:
            from flask import make_response
            resp = make_response({"status": "failed", "error": "No file uploaded"})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        
        file = request.files['file']
        print(f"File received: {file.filename}")
        if file.filename == '':
            from flask import make_response
            resp = make_response({"status": "failed", "error": "No file selected"})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        
        # Save the uploaded file temporarily
        import os
        # Get file extension from uploaded file
        file_extension = os.path.splitext(file.filename)[1] or '.jpg'
        temp_path = f"/tmp/temp_upload_{int(time.time())}{file_extension}"

        # Save file with proper error handling
        try:
            # Save the file
            file.save(temp_path)
            
            # Verify file was saved correctly
            if not os.path.exists(temp_path):
                raise Exception("File was not saved to disk")
            
            file_size = os.path.getsize(temp_path)
            print(f"File saved successfully: {temp_path}, size: {file_size} bytes")
            
            if file_size == 0:
                raise Exception("Saved file is empty")
                
            # Try to verify PIL can read it
            from PIL import Image
            with Image.open(temp_path) as test_img:
                print(f"PIL verification successful: {test_img.format}, size: {test_img.size}")
                
        except Exception as save_error:
            print(f"File saving/verification error: {save_error}")
            # Try alternative saving method
            temp_path = f"/tmp/temp_upload_alt_{int(time.time())}{file_extension}"
            with open(temp_path, 'wb') as f:
                file.seek(0)  # Reset file pointer
                f.write(file.read())
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            
            file_size = os.path.getsize(temp_path)
            print(f"Alternative save method: {temp_path}, size: {file_size} bytes")

        # Process the uploaded file
        detected_text, text_segments, output_filename = detect_text(temp_path)
        print("Detection completed successfully")
        
        # Calculate processing time and accuracy for metrics
        processing_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        accuracy_score = calculate_accuracy_score(detected_text)
        
        # Generate unique invoice ID and store metrics
        invoice_id = f"inv_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        store_metrics(invoice_id, processing_time, accuracy_score)
        
        # Broadcast updated metrics to connected dashboards
        from app import broadcast_metrics_to_all
        broadcast_metrics_to_all()

        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        ## processing text 
        from flask import make_response
        response = {
            "status": "success", 
            "image_url": f"/tmp/{output_filename}", 
            "extracted_text": detected_text,
            "text_segments": text_segments,
            "processing_time_ms": processing_time,
            "accuracy_score": accuracy_score,
            "invoice_id": invoice_id
        }
        resp = make_response(response)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp
    except Exception as e:
        print(f"Exception error: {str(e)}")
        import traceback 
        traceback.print_exc()
        from flask import make_response
        error_response = {"status": "failed", "error": str(e)}
        resp = make_response(error_response)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp
        #Return a JSON response with the new image’s URL:


##Those ADC tokens only live for a short time (often an hour, or up to a week if you used gcloud auth application-default login). After that, they’re dead—and any API call using them will fail with invalid_grant.


