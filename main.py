from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import os


app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login")
def loginPage():
    return render_template("login.html")

@app.route("/uploadImages", methods=['GET', 'POST'])
def uploadImages():
    if request.method == 'POST':
        # Retrieve files from form
        fileFront = request.files.get('fileInputFront')
        fileBack = request.files.get('fileInputBack')
        fileLeft = request.files.get('fileInputLeft')
        fileRight = request.files.get('fileInputRight')

        # Save the uploaded files to the upload folder and read them with OpenCV
        if fileFront:
            filenameFront = secure_filename(fileFront.filename)
            filepathFront = os.path.join(app.config['UPLOAD_FOLDER'], filenameFront)
            fileFront.save(filepathFront)
            imgFront = cv2.imread(filepathFront)
            if imgFront is None:
                return "Error: Unable to read uploaded front image."

        if fileBack:
            filenameBack = secure_filename(fileBack.filename)
            filepathBack = os.path.join(app.config['UPLOAD_FOLDER'], filenameBack)
            fileBack.save(filepathBack)
            imgBack = cv2.imread(filepathBack)
            if imgBack is None:
                return "Error: Unable to read uploaded back image."

        if fileLeft:
            filenameLeft = secure_filename(fileLeft.filename)
            filepathLeft = os.path.join(app.config['UPLOAD_FOLDER'], filenameLeft)
            fileLeft.save(filepathLeft)
            imgLeft = cv2.imread(filepathLeft)
            if imgLeft is None:
                return "Error: Unable to read uploaded left image."

        if fileRight:
            filenameRight = secure_filename(fileRight.filename)
            filepathRight = os.path.join(app.config['UPLOAD_FOLDER'], filenameRight)
            fileRight.save(filepathRight)
            imgRight = cv2.imread(filepathRight)
            if imgRight is None:
                return "Error: Unable to read uploaded right image."


    return render_template("uploadImages.html")
@app.route("/get_coordinates",methods=['POST'])
def get_coordinates():
    data = request.json
    x =data['x']
    y = data['y']
    print("Clicked coordinates: ({}, {})".format(x, y))
    return jsonify({"message": "Coordinates received successfully."})


if __name__ == '__main__':
    app.run(debug=True)
