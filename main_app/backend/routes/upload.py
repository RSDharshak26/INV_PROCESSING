from flask import Blueprint, request
from dotenv import load_dotenv
load_dotenv()


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
    texts = response.text_annotations
    print("Texts:")

    detected_texts = []
    for text in texts:
        print(f'\n"{text.description}"')
        detected_texts.append(text.description)

        vertices = [
            f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices
        ]

        print("bounds: {}".format(",".join(vertices)))
    

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )
    
    return detected_texts



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
        print(detected_text)
        return {"status": "success", "detected_text": detected_text}
    except Exception as e:
        print("exception error")
        import traceback 
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


##Those ADC tokens only live for a short time (often an hour, or up to a week if you used gcloud auth application-default login). After that, they’re dead—and any API call using them will fail with invalid_grant.


