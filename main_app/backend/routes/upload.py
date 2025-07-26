from flask import Blueprint, request
from PIL import Image, ImageDraw
from dotenv import load_dotenv
load_dotenv()
import time
import re

upload_bp = Blueprint('upload', __name__)


def detect_text(path):
    """Detects text in the file."""
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()

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
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    for text in texts:
        # Get the bounding box vertices as a list of (x, y) tuples
        vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
        if len(vertices) == 4:
            draw.line(vertices + [vertices[0]], width=2, fill='red')  # Draw box
    # Save the image with boxes in tmp directory for Lambda
    output_path = f"/tmp/{output_filename}"
    image.save(output_path)
    print(f"Image saved to: {output_path}")

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
        file.save(temp_path)
        print("File saved successfully")
        
        # Process the uploaded file
        detected_text, text_segments, output_filename = detect_text(temp_path)
        print("Detection completed successfully")
        
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        ## processing text 
        from flask import make_response
        response = {
            "status": "success", 
            "image_url": f"/tmp/{output_filename}", 
            "extracted_text": detected_text,
            "text_segments": text_segments
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


