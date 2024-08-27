from flask import Flask, render_template, request, jsonify, redirect, url_for, g
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import os
import base64
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, delete, select
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import redis
import boto3
import io
from urllib.parse import urlparse
from flask_session import Session

app = Flask(__name__, static_folder='static')

# Set the SECRET_KEY for securely signing the session cookie
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:Halotop002%3F@alignwizarddb.cbmaie42gjxa.us-east-2.rds.amazonaws.com:5432/alignDB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'session:'
app.config['SESSION_REDIS'] = redis.StrictRedis(host='localhost', port=6379, db=0)
CLOUDFRONT_TO_S3_BUCKET = {
    'd12345abcdefg.cloudfront.net': 'your-s3-bucket-name'
}
# Initialize Flask-Session
Session(app)

# AWS S3 configuration
S3_BUCKET = 'postureimagebucket'
S3_REGION = 'us-east-2'
s3 = boto3.client('s3', region_name=S3_REGION)
s3_client = boto3.client('s3', region_name=S3_REGION)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'loginPage'
GLOBAL_IMAGES_KEY = "globalImages"
SAVED_IMAGES_KEY = "savedImages"
# CloudFront domain
CLOUDFRONT_DOMAIN = os.environ.get('CLOUDFRONT_DOMAIN', 'd18t3ps388njbv.cloudfront.net')

# Set up logging
if not app.debug:
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

# Function to delete an object from S3

def delete_s3_object(url):
    try:
        parsed_url = urlparse(url)
        cloudfront_domain = parsed_url.netloc
        key = parsed_url.path.lstrip('/')

        # Map CloudFront domain to S3 bucket name
        bucket_name = CLOUDFRONT_TO_S3_BUCKET.get(cloudfront_domain)
        if not bucket_name:
            raise ValueError(f"No S3 bucket mapping found for CloudFront domain: {cloudfront_domain}")

        app.logger.info(f"Deleting object from S3 - Bucket: {bucket_name}, Key: {key}")
        s3_client.delete_object(Bucket=bucket_name, Key=key)
        app.logger.info(f"Deleted {key} from {bucket_name}")
    except Exception as e:
        app.logger.error(f"Error deleting object {key} from {bucket_name}: {e}")

# Function to upload to S3
def upload_to_s3(file, user_id, patient_id, filename, bucket_name):
    try:
        unique_filename = f"{user_id}_{patient_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        app.logger.info(f"Uploading {unique_filename} to S3 bucket {bucket_name}")
        s3_client.upload_fileobj(file, bucket_name, unique_filename, ExtraArgs={"ContentType": "image/jpeg"})
        app.logger.info(f"Successfully uploaded {unique_filename} to S3")
    except Exception as e:
        app.logger.error(f"Failed to upload {filename} to S3: {e}")
        return None
    cloudfront_url = f"https://{CLOUDFRONT_DOMAIN}/{unique_filename}"
    return cloudfront_url

# Helper function to get Redis client
def get_redis_client():
    if 'redis_client' not in g:
        g.redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    return g.redis_client

# Helper function to generate user-specific Redis keys
def generate_redis_key(base_key):
    return f"{current_user.id}_{base_key}"

# Helper functions to interact with Redis
def get_global_image(redis_client, image_key):
    user_key = generate_redis_key(image_key)
    image_data = redis_client.hget(GLOBAL_IMAGES_KEY, user_key)
    if image_data:
        np_arr = np.frombuffer(base64.b64decode(image_data), np.uint8)
        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return None

def set_global_image(redis_client, image_key, image):
    user_key = generate_redis_key(image_key)
    _, buffer = cv2.imencode('.png', image)
    image_data = base64.b64encode(buffer).decode('utf-8')
    redis_client.hset(GLOBAL_IMAGES_KEY, user_key, image_data)

def get_saved_image(redis_client, image_key):
    user_key = generate_redis_key(image_key)
    image_data = redis_client.hget(SAVED_IMAGES_KEY, user_key)
    if image_data:
        np_arr = np.frombuffer(base64.b64decode(image_data), np.uint8)
        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return None

def set_saved_image(redis_client, image_key, image):
    user_key = generate_redis_key(image_key)
    _, buffer = cv2.imencode('.png', image)
    image_data = base64.b64encode(buffer).decode('utf-8')
    redis_client.hset(SAVED_IMAGES_KEY, user_key, image_data)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    patients = db.relationship('Patient', backref='user', lazy=True)
    imageNum =db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<User {self.name}>'

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    images = db.relationship('Image', backref='patient', lazy=True)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    image_front = db.Column(db.String, nullable=False)  # URL instead of binary
    image_back = db.Column(db.String, nullable=False)   # URL instead of binary
    image_left = db.Column(db.String, nullable=False)   # URL instead of binary
    image_right = db.Column(db.String, nullable=False)  # URL instead of binary
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)

def addUser(name, email, password):
    password_hash = generate_password_hash(password)
    new_user = User(name=name, password_hash=password_hash, email=email)
    db.session.add(new_user)
    db.session.commit()
    app.logger.info(f"User {name} added successfully!")

def addPatient(patientName, userID):
    new_patient = Patient(patient_name=patientName, user_id=userID)
    db.session.add(new_patient)
    db.session.commit()
    app.logger.info(f"Patient {patientName} added successfully!")

def addImage(front, back, left, right, patientID):
    _, buffer = cv2.imencode('.jpg', front)
    frontBlob = buffer.tobytes()
    _, buffer = cv2.imencode('.jpg', back)
    backBlob = buffer.tobytes()
    _, buffer = cv2.imencode('.jpg', left)
    leftBlob = buffer.tobytes()
    _, buffer = cv2.imencode('.jpg', right)
    rightBlob = buffer.tobytes()
    new_images = Image(image_front=frontBlob, image_back=backBlob, image_left=leftBlob, image_right=rightBlob, patient_id=patientID)
    db.session.add(new_images)
    db.session.commit()
    app.logger.info("Images added successfully!")

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def scale_coordinates(x, y, display_width, display_height, actual_width, actual_height):
    scaled_x = int(x * actual_width / display_width)
    scaled_y = int(y * actual_height / display_height)
    return scaled_x, scaled_y

def drawCross(img, x, y, display_width, display_height):
    h, w, _ = img.shape
    x, y = scale_coordinates(x, y, display_width, display_height, w, h)
    x = max(0, min(w - 1, x))
    y = max(0, min(h - 1, y))
    cv2.line(img, (x, 0), (x, h - 1), (0, 0, 0), 5)
    cv2.line(img, (0, y), (w - 1, y), (0, 0, 0), 5)
    return img

def base64_to_image(base64_str):
    img_data = base64.b64decode(base64_str.split(',')[1])
    np_arr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img

def image_to_base64(image):
    _, buffer = cv2.imencode('.png', image)
    base64_image = base64.b64encode(buffer).decode('utf-8')
    return base64_image

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('findPatient'))
    return render_template("index.html")

@app.route("/homeLogged")
def homeLogged():
    return render_template("homeLogged.html")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('loginPage'))

@app.route("/login")
def loginPage():
    return render_template("login.html")

@app.route("/signUp")
def signUp():
    return render_template("signUp.html")

@app.route("/findPatient", methods=['GET'])
def findPatient():
    patientList = db.session.execute(db.select(Patient.patient_name).filter_by(user_id=current_user.id)).scalars().all()
    app.logger.info(f"Patient list for user {current_user.id}: {patientList}")
    return render_template("findPatient.html", patientList=patientList)

@app.route("/patientHome")
def patientHome():
    patient_name = request.args.get('data')
    patient = db.session.execute(
        db.select(Patient).filter_by(patient_name=patient_name, user_id=current_user.id)
    ).scalar_one_or_none()

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    patient_images = db.session.execute(
        db.select(Image).filter_by(patient_id=patient.id).order_by(Image.date_created.desc())
    ).scalars().all()

    image_data = []
    for image in patient_images:
        image_data.append({
            "id": image.id,
            "date": image.date_created,
            "frontImage": image.image_front,
            "backImage": image.image_back,
            "leftImage": image.image_left,
            "rightImage": image.image_right
        })

    return render_template("patientHome.html", data=image_data)

@app.route("/compareImages")
def compareImages():
    id1 = request.args.get('date1')
    id2 = request.args.get('date2')
    patient = request.args.get('patient')
    patient_images = db.session.execute(
        db.select(Image).filter(or_(Image.id == id1, Image.id == id2)).order_by(Image.date_created.desc())
    ).scalars().all()

    image_data = []
    for image in patient_images:
        image_data.append({
            "id": image.id,
            "date": image.date_created,
            "frontImage": image.image_front,
            "backImage": image.image_back,
            "leftImage": image.image_left,
            "rightImage": image.image_right
        })

    return render_template("compareImages.html", data=image_data)

@app.route("/enterNewPatient")
def enterNewPatient():
    return render_template("enterNewPatient.html")

@app.route("/getUser", methods=['POST'])
def getUser():
    data = request.json
    email = data.get('email')
    email = email.lower()
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return jsonify({"message": "User authenticated successfully"}), 200
    return jsonify({"error": "Incorrect email or password"}), 401

@app.route("/createUser", methods=['POST'])
def createUser():
    data = request.json
    email = data['email']
    email = email.lower()
    password = data['password']
    name = data['name']
    nameTaken = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if nameTaken:
        return jsonify({"error": "email is taken"}), 401
    addUser(name, email, password)
    return jsonify({"message": "new user received"})

@app.route("/createPatient", methods=['POST'])
def createPatient():
    data = request.json
    patientName = data['patient']
    nameTaken = db.session.execute(db.select(Patient).filter_by(user_id=current_user.id).filter_by(patient_name=patientName)).scalar_one_or_none()
    if nameTaken:
        return jsonify({"error": "name is taken"}), 401
    addPatient(patientName, current_user.id)
    return jsonify({"message": "new patient received"})

@app.route("/uploadImages", methods=['GET', 'POST'])
@login_required
def uploadImages():
    redis_client = get_redis_client()
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
            set_global_image(redis_client, 'imgFront', imgFront)
        if fileBack:
            filenameBack = secure_filename(fileBack.filename)
            filepathBack = os.path.join(app.config['UPLOAD_FOLDER'], filenameBack)
            fileBack.save(filepathBack)
            imgBack = cv2.imread(filepathBack)
            if imgBack is None:
                return "Error: Unable to read uploaded back image."
            set_global_image(redis_client, 'imgBack', imgBack)
        if fileLeft:
            filenameLeft = secure_filename(fileLeft.filename)
            filepathLeft = os.path.join(app.config['UPLOAD_FOLDER'], filenameLeft)
            fileLeft.save(filepathLeft)
            imgLeft = cv2.imread(filepathLeft)
            if imgLeft is None:
                return "Error: Unable to read uploaded left image."
            set_global_image(redis_client, 'imgLeft', imgLeft)
        if fileRight:
            filenameRight = secure_filename(fileRight.filename)
            filepathRight = os.path.join(app.config['UPLOAD_FOLDER'], filenameRight)
            fileRight.save(filepathRight)
            imgRight = cv2.imread(filepathRight)
            if imgRight is None:
                return "Error: Unable to read uploaded right image."
            set_global_image(redis_client, 'imgRight', imgRight)
    return render_template("uploadImages.html")

@app.route("/saveImages", methods=['POST'])
def saveImages():
    redis_client = get_redis_client()
    data = request.json
    patientName = data['patientData']
    numImg = db.session.execute(
        db.select(User.imageNum)
        .filter_by(id=current_user.id)
    ).scalar_one_or_none()
    if numImg >= 2000:
        return jsonify({"error": "Reached Image Limit"}), 400

    # Generate a unique set_id based on the current timestamp
    set_id = datetime.now().strftime("%Y%m%d%H%M%S")

    # Find the patient by name and current user
    patient = db.session.execute(db.select(Patient).filter_by(patient_name=patientName, user_id=current_user.id)).scalar()
    if not patient:
        app.logger.error(f"Patient {patientName} not found for user {current_user.id}")
        return jsonify({"error": "Patient not found"}), 404

    front_image = get_saved_image(redis_client, 'front')
    back_image = get_saved_image(redis_client, 'back')
    left_image = get_saved_image(redis_client, 'left')
    right_image = get_saved_image(redis_client, 'right')

    # Check if any image is None
    if front_image is None or back_image is None or left_image is None or right_image is None:
        app.logger.error(f"One or more images are missing for user {current_user.id}")
        return jsonify({"error": "One or more images are missing"}), 400

    # Encode images to JPEG and upload to S3
    try:
        front_image_bytes = io.BytesIO(cv2.imencode('.jpg', front_image)[1])
        back_image_bytes = io.BytesIO(cv2.imencode('.jpg', back_image)[1])
        left_image_bytes = io.BytesIO(cv2.imencode('.jpg', left_image)[1])
        right_image_bytes = io.BytesIO(cv2.imencode('.jpg', right_image)[1])

        front_image_url = upload_to_s3(front_image_bytes, current_user.id, patient.id, 'front.jpg', S3_BUCKET)
        back_image_url = upload_to_s3(back_image_bytes, current_user.id, patient.id, 'back.jpg', S3_BUCKET)
        left_image_url = upload_to_s3(left_image_bytes, current_user.id, patient.id, 'left.jpg', S3_BUCKET)
        right_image_url = upload_to_s3(right_image_bytes, current_user.id, patient.id, 'right.jpg', S3_BUCKET)

        # Check if all URLs are generated
        if not all([front_image_url, back_image_url, left_image_url, right_image_url]):
            app.logger.error(f"Failed to upload one or more images to S3 for user {current_user.id}")
            return jsonify({"error": "Failed to upload one or more images to S3"}), 500

        # Save URLs in the database
        new_image_record = Image(
            image_front=front_image_url,
            image_back=back_image_url,
            image_left=left_image_url,
            image_right=right_image_url,
            patient_id=patient.id
        )
        current_user.imageNum += 4
        db.session.add(new_image_record)
        db.session.commit()

        app.logger.info(f"Successfully uploaded images and saved to database for user {current_user.id}")

        # Clear Redis keys for the current user
        redis_client.hdel(GLOBAL_IMAGES_KEY, generate_redis_key('front'))
        redis_client.hdel(GLOBAL_IMAGES_KEY, generate_redis_key('back'))
        redis_client.hdel(GLOBAL_IMAGES_KEY, generate_redis_key('left'))
        redis_client.hdel(GLOBAL_IMAGES_KEY, generate_redis_key('right'))
        redis_client.hdel(SAVED_IMAGES_KEY, generate_redis_key('front'))
        redis_client.hdel(SAVED_IMAGES_KEY, generate_redis_key('back'))
        redis_client.hdel(SAVED_IMAGES_KEY, generate_redis_key('left'))
        redis_client.hdel(SAVED_IMAGES_KEY, generate_redis_key('right'))




        return jsonify({"message": "Successful Image Upload", "set_id": set_id})

    except Exception as e:
        app.logger.error(f"An error occurred during image upload and save process for user {current_user.id}: {e}")
        return jsonify({"error": "An error occurred during the image upload process"}), 500

@app.route("/deleteImages")
def deleteImages():
    patient = request.args.get('data')
    patient_id = db.session.execute(
        db.select(Patient.id).filter_by(patient_name=patient, user_id=current_user.id)
    ).scalar_one_or_none()

    if not patient_id:
        return jsonify({"error": "Patient not found"}), 404

    patient_images = db.session.execute(
        db.select(Image).filter_by(patient_id=patient_id).order_by(Image.date_created.desc())
    ).scalars().all()

    image_data = []
    for image in patient_images:
        image_data.append({
            "id": image.id,
            "date": image.date_created,
            "frontImage": image.image_front,
            "backImage": image.image_back,
            "leftImage": image.image_left,
            "rightImage": image.image_right
        })

    return render_template("deleteImages.html", data=image_data)
@app.route("/removeImages", methods=["POST"])
def removeImages():
    data = request.json
    imageIds = data['dates']

    for id in imageIds:
        # Fetch the image record using SQLAlchemy Core
        image_record = db.session.execute(select(Image).filter_by(id=id)).scalar_one_or_none()

        if image_record:
            # Delete the objects from S3
            delete_s3_object(image_record.image_front)
            delete_s3_object(image_record.image_back)
            delete_s3_object(image_record.image_left)
            delete_s3_object(image_record.image_right)

            # Delete the record from the database
            db.session.execute(delete(Image).filter_by(id=id))
            db.session.commit()
        else:
            app.logger.error(f"Image with ID {id} not found")

    return jsonify({"message": "Images Deleted"}), 200

@app.route("/get_coordinatesFront", methods=['POST'])
def get_coordinatesFront():
    redis_client = get_redis_client()
    data = request.json
    x = data['xFront']
    y = data['yFront']
    width = data['width']
    height = data['height']
    app.logger.info(f"Received coordinates for front: ({x}, {y}), width: {width}, height: {height}")

    imgFront = get_global_image(redis_client, 'imgFront')
    if imgFront is not None:
        img_copy = imgFront.copy()
        processed_image = drawCross(img_copy, x, y, width, height)
        set_saved_image(redis_client, "front", processed_image)

        return jsonify({"message": "Coordinates received successfully."})
    else:
        app.logger.error("imgFront not found in globalImages")
        return jsonify({"error": "imgFront not found"}), 400

@app.route("/uploadFront", methods=['POST'])
def uploadFront():
    redis_client = get_redis_client()
    data = request.json
    img_front_base64 = data['imgFront']
    imgFront = base64_to_image(img_front_base64)
    set_global_image(redis_client, 'imgFront', imgFront)
    set_saved_image(redis_client, 'front', imgFront)
    return jsonify({"message": "Front image received successfully."})

@app.route("/get_coordinatesBack", methods=['POST'])
def get_coordinatesBack():
    redis_client = get_redis_client()
    data = request.json
    x = data['xBack']
    y = data['yBack']
    width = data['width']
    height = data['height']
    app.logger.info(f"Received coordinates for back: ({x}, {y}), width: {width}, height: {height}")

    imgBack = get_global_image(redis_client, 'imgBack')
    if imgBack is not None:
        img_copy = imgBack.copy()
        processed_image = drawCross(img_copy, x, y, width, height)
        set_saved_image(redis_client, "back", processed_image)

        return jsonify({"message": "Coordinates received successfully."})
    else:
        app.logger.error("imgBack not found in globalImages")
        return jsonify({"error": "imgBack not found"}), 400

@app.route("/uploadBack", methods=['POST'])
def uploadBack():
    redis_client = get_redis_client()
    data = request.json
    img_back_base64 = data['imgBack']
    imgBack = base64_to_image(img_back_base64)
    set_global_image(redis_client, 'imgBack', imgBack)
    set_saved_image(redis_client, 'back', imgBack)
    return jsonify({"message": "Back image received successfully."})

@app.route("/get_coordinatesLeft", methods=['POST'])
def get_coordinatesLeft():
    redis_client = get_redis_client()
    data = request.json
    x = data['xLeft']
    y = data['yLeft']
    width = data['width']
    height = data['height']
    app.logger.info(f"Received coordinates for left: ({x}, {y}), width: {width}, height: {height}")

    imgLeft = get_global_image(redis_client, 'imgLeft')
    if imgLeft is not None:
        img_copy = imgLeft.copy()
        processed_image = drawCross(img_copy, x, y, width, height)
        set_saved_image(redis_client, "left", processed_image)

        return jsonify({"message": "Coordinates received successfully."})
    else:
        app.logger.error("imgLeft not found in globalImages")
        return jsonify({"error": "imgLeft not found"}), 400

@app.route("/uploadLeft", methods=['POST'])
def uploadLeft():
    redis_client = get_redis_client()
    data = request.json
    img_left_base64 = data['imgLeft']
    imgLeft = base64_to_image(img_left_base64)
    set_global_image(redis_client, 'imgLeft', imgLeft)
    set_saved_image(redis_client, 'left', imgLeft)
    return jsonify({"message": "Left image received successfully."})

@app.route("/get_coordinatesRight", methods=['POST'])
def get_coordinatesRight():
    redis_client = get_redis_client()
    data = request.json
    x = data['xRight']
    y = data['yRight']
    width = data['width']
    height = data['height']
    app.logger.info(f"Received coordinates for right: ({x}, {y}), width: {width}, height: {height}")

    imgRight = get_global_image(redis_client, 'imgRight')
    if imgRight is not None:
        img_copy = imgRight.copy()
        processed_image = drawCross(img_copy, x, y, width, height)
        set_saved_image(redis_client, "right", processed_image)

        return jsonify({"message": "Coordinates received successfully."})
    else:
        app.logger.error("imgRight not found in globalImages")
        return jsonify({"error": "imgRight not found"}), 400

@app.route("/uploadRight", methods=['POST'])
def uploadRight():
    redis_client = get_redis_client()
    data = request.json
    img_right_base64 = data['imgRight']
    imgRight = base64_to_image(img_right_base64)
    set_global_image(redis_client, 'imgRight', imgRight)
    set_saved_image(redis_client, 'right', imgRight)
    return jsonify({"message": "Right image received successfully."})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False)  # Ensure debug is False for production

