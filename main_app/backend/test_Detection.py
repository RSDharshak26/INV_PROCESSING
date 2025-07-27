from dotenv import load_dotenv
load_dotenv()
from PIL import Image, ImageDraw
import boto3
import json
from botocore.exceptions import ClientError

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
    texts = response.text_annotations
    print("Texts:")
    for text in texts: # every detection produces a desccription and bounding boxes
        print(f'\n"{text.description}"')
        vertices = [
            f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices
        ]
        print("bounds: {}".format(",".join(vertices)))
    
    draw_boxes_on_image(path, texts)
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


detect_text(r'C:\Users\rsdha\Documents\GitHub\INV_PROCESSING\main_app\images\inv_example_1.jpg')
