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
    for text in texts: # every detection produces a desccription and bounding boxes
        print(f'\n"{text.description}"')
        vertices = [
            f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices
        ]
        print("bounds: {}".format(",".join(vertices)))
    
    
    draw_boxes_on_image(path, texts)
    output_filename = f"output_with_boxes_{int(time.time())}.jpg"
    image.save("main_app/backend/static/{output_filename}.jpg")
    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )



def draw_boxes_on_image(image_path, texts):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    for text in texts:
        # Get the bounding box vertices as a list of (x, y) tuples
        vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
        if len(vertices) == 4:
            draw.line(vertices + [vertices[0]], width=2, fill='red')  # Draw box
    # Save or show the image
    image.show()  # To display
    # image.save("output_with_boxes.jpg")  # To save

##pip install flask-cors. this is to let 2 ports to talk to each other 

@upload_bp.route('/receive', methods=['GET','POST'])
def receive_image():
    #file = request.files[]   # matches formData.append('file', file)
    # file is a FileStorage object you can .save(), read .stream, etc.

    print("data received")
    try:
        detected_text=detect_text(r'C:\Users\rsdha\Documents\GitHub\INV_PROCESSING\main_app\images\inv_example_1.jpg')
        ##detected_text = detect_text('C:\Users\rsdha\Documents\GitHub\INV_PROCESSING\main_app\images\inv_example_1.jpg')
        print("detection is ongoing")
        
        ## processing text 
        lines = detected_text.splitlines()
        print(detected_text)
        return {"status": "success", "detected_text": detected_text}
    except Exception as e:
        print("exception error")
        import traceback 
        traceback.print_exc()
        return {"status": "success", "image_url": f"/static/{output_filename}"}


##Those ADC tokens only live for a short time (often an hour, or up to a week if you used gcloud auth application-default login). After that, they’re dead—and any API call using them will fail with invalid_grant.


