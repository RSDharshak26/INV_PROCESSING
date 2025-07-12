from dotenv import load_dotenv
load_dotenv()
from PIL import Image, ImageDraw

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
