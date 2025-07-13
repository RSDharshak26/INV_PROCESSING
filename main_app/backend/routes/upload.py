from flask import Blueprint, request
from PIL import Image, ImageDraw
upload_bp = Blueprint('upload', __name__)
import time
from dotenv import load_dotenv
load_dotenv()

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
    texts = response.text_annotations
    print("Texts:")
    detected_text = ""
    for text in texts: # every detection produces a desccription and bounding boxes
        print(f'\n"{text.description}"')
        detected_text += text.description + "\n"
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
    
    return detected_text, output_filename



def draw_boxes_on_image(image_path, texts, output_filename):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    for text in texts:
        # Get the bounding box vertices as a list of (x, y) tuples
        vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
        if len(vertices) == 4:
            draw.line(vertices + [vertices[0]], width=2, fill='red')  # Draw box
    # Save the image with boxes
    output_path = f"static/{output_filename}"
    image.save(output_path)
    print(f"Image saved to: {output_path}")

##pip install flask-cors. this is to let 2 ports to talk to each other 

@upload_bp.route('/receive', methods=['GET','POST'])
def receive_image():
    print("data received")
    
    if 'file' not in request.files:
        return {"status": "failed", "error": "No file uploaded"}
    
    file = request.files['file']
    if file.filename == '':
        return {"status": "failed", "error": "No file selected"}
    
    try:
        # Save the uploaded file temporarily
        import os
        temp_path = f"temp_upload_{int(time.time())}.pdf"
        file.save(temp_path)
        
        # Process the uploaded file
        detected_text, output_filename = detect_text(temp_path)
        print("detection is ongoing")
        
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        ## processing text 
        print(detected_text)
        return {"status": "success", "image_url": f"/static/{output_filename}"}
    except Exception as e:
        print("exception error")
        import traceback 
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}
        #Return a JSON response with the new image’s URL:


##Those ADC tokens only live for a short time (often an hour, or up to a week if you used gcloud auth application-default login). After that, they’re dead—and any API call using them will fail with invalid_grant.


