from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import os
import base64

app = Flask(__name__)

globalImages = {}

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def scale_coordinates(x, y, display_width, display_height, actual_width, actual_height):
    scaled_x = int(x * actual_width / display_width)
    scaled_y = int(y * actual_height / display_height)
    return scaled_x, scaled_y

def drawCross(img, x, y):
    h, w, _ = img.shape

    # These should be the dimensions of the image as displayed in the HTML
    display_width = 600
    display_height = 600

    x, y = scale_coordinates(x, y, display_width, display_height, w, h)  # Swap h and w here

    print("Image dimensions: height =", h, "width =", w)
    print("Scaled coordinates: x =", x, "y =", y)

    # Ensure x and y are within bounds
    x = max(0, min(w - 1, x))
    y = max(0, min(h - 1, y))

    # Draw vertical line from top to bottom
    cv2.line(img, (x, 0), (x, h - 1), (0, 0, 0), 5)

    # Draw horizontal line from left to right
    cv2.line(img, (0, y), (w - 1, y), (0, 0, 0), 5)

    return img

def base64_to_image(base64_str):
    img_data = base64.b64decode(base64_str.split(',')[1])  # remove the `data:image/...` part
    np_arr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img

def image_to_base64(image):
    _, buffer = cv2.imencode('.png', image)
    base64_image = base64.b64encode(buffer).decode('utf-8')
    return base64_image

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login")
def loginPage():
    return render_template("login.html")

@app.route("/uploadImages", methods=['GET', 'POST'])
def uploadImages():
    if request.method == 'POST':
        fileFront = request.files.get('fileInputFront')
        fileBack = request.files.get('fileInputBack')
        fileLeft = request.files.get('fileInputLeft')
        fileRight = request.files.get('fileInputRight')

        if fileFront:
            filenameFront = secure_filename(fileFront.filename)
            filepathFront = os.path.join(app.config['UPLOAD_FOLDER'], filenameFront)
            fileFront.save(filepathFront)
            imgFront = cv2.imread(filepathFront)
            if imgFront is None:
                return "Error: Unable to read uploaded front image."
            globalImages['imgFront'] = imgFront  # Save the original image

        if fileBack:
            filenameBack = secure_filename(fileBack.filename)
            filepathBack = os.path.join(app.config['UPLOAD_FOLDER'], filenameBack)
            fileBack.save(filepathBack)
            imgBack = cv2.imread(filepathBack)
            if imgBack is None:
                return "Error: Unable to read uploaded back image."
            globalImages['imgBack'] = imgBack  # Save the original image

        if fileLeft:
            filenameLeft = secure_filename(fileLeft.filename)
            filepathLeft = os.path.join(app.config['UPLOAD_FOLDER'], filenameLeft)
            fileLeft.save(filepathLeft)
            imgLeft = cv2.imread(filepathLeft)
            if imgLeft is None:
                return "Error: Unable to read uploaded left image."
            globalImages['imgLeft'] = imgLeft  # Save the original image

        if fileRight:
            filenameRight = secure_filename(fileRight.filename)
            filepathRight = os.path.join(app.config['UPLOAD_FOLDER'], filenameRight)
            fileRight.save(filepathRight)
            imgRight = cv2.imread(filepathRight)
            if imgRight is None:
                return "Error: Unable to read uploaded right image."
            globalImages['imgRight'] = imgRight  # Save the original image

    return render_template("uploadImages.html")

@app.route("/get_coordinatesFront", methods=['POST'])
def get_coordinatesFront():
    data = request.json
    x = data['xFront']
    y = data['yFront']
    print(x, y)

    # Use a copy of the original image to draw the cross
    img_copy = globalImages['imgFront'].copy()
    processed_image = drawCross(img_copy, x, y)
    base64_image = image_to_base64(processed_image)

    return jsonify({"message": "Coordinates received successfully.", "image": base64_image})

@app.route("/uploadFront", methods=['POST'])
def uploadFront():
    data = request.json
    img_front_base64 = data['imgFront']
    globalImages['imgFront'] = base64_to_image(img_front_base64)

    return jsonify({"message": "Front image received successfully."})

@app.route("/get_coordinatesBack", methods=['POST'])
def get_coordinatesBack():
    data = request.json
    x = data['xBack']
    y = data['yBack']

    print("Clicked coordinates: ({}, {})".format(x, y))
    return jsonify({"message": "Coordinates received successfully."})

@app.route("/get_coordinatesLeft", methods=['POST'])
def get_coordinatesLeft():
    data = request.json
    x = data['xLeft']
    y = data['yLeft']

    print("Clicked coordinates: ({}, {})".format(x, y))
    return jsonify({"message": "Coordinates received successfully."})

@app.route("/get_coordinatesRight", methods=['POST'])
def get_coordinatesRight():
    data = request.json
    x = data['xRight']
    y = data['yRight']

    print("Clicked coordinates: ({}, {})".format(x, y))
    return jsonify({"message": "Coordinates received successfully."})

if __name__ == '__main__':
    app.run(debug=True)

