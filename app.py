from flask import Flask, render_template, request, jsonify, redirect, url_for
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import os
import base64
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from datetime import datetime




app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY']= "myKey"
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:password@localhost/postgres'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'loginPage'
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)

    password_hash = db.Column(db.String(200), nullable=False)

    # Relationship to link User to their Patients
    patients = db.relationship('Patient', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.name}>'

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(150),  nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship to link Patient to their Images
    images = db.relationship('Image', backref='patient', lazy=True)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    image_front = db.Column(db.LargeBinary)
    image_back = db.Column(db.LargeBinary)
    image_left = db.Column(db.LargeBinary)
    image_right = db.Column(db.LargeBinary)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
def addUser(name,email, password):
    password_hash = generate_password_hash(password)
    new_user = User(name=name, password_hash=password_hash, email = email)
    db.session.add(new_user)
    db.session.commit()
    print(f"User {name} added successfully!")
def addPatient(patientName, userID):
    new_patient = Patient(patient_name=patientName, user_id=userID)
    db.session.add(new_patient)
    db.session.commit()
    print(f"User {patientName} added successfully!")
def addImage(front,back,left,right,patientID):
    _, buffer = cv2.imencode('.jpg', front)
    frontBlob = buffer.tobytes()
    _, buffer = cv2.imencode('.jpg', back)
    backBlob = buffer.tobytes()
    _, buffer = cv2.imencode('.jpg', left)
    leftBlob = buffer.tobytes()
    _, buffer = cv2.imencode('.jpg', right)
    rightBlob = buffer.tobytes()
    new_Images = Image(image_front=frontBlob,image_back=backBlob,image_left=leftBlob,image_right=rightBlob, patient_id=patientID)
    db.session.add(new_Images)
    db.session.commit()
    print(f" images added successfully!")
globalImages = {}
savedImages = {}
name = ''
password = ''
email = ''

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def scale_coordinates(x, y, display_width, display_height, actual_width, actual_height):
    scaled_x = int(x * actual_width / display_width)
    scaled_y = int(y * actual_height / display_height)
    return scaled_x, scaled_y

def drawCross(img, x, y,display_width,display_height):
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
        return redirect(url_for('homeLogged'))
    return render_template("home.html")
@app.route("/homeLogged")
def homeLogged():
    return render_template("homeLogged.html")
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User,int(user_id))
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
@app.route("/findPatient",methods=['GET'])
def findPatient():
    patientList = db.session.execute(db.select(Patient.patient_name).filter_by(user_id=current_user.id)).scalars().all()
    print(patientList)

    return render_template("findPatient.html",patientList=patientList)


@app.route("/patientHome")
def patientHome():
    patient = request.args.get('data')
    patientid = db.session.execute(
        db.select(Patient.id).filter_by(patient_name=patient, user_id=current_user.id)
    ).scalar_one()

    print(patient)

    patientImages = db.session.execute(
        db.select(Image).filter_by(patient_id=patientid).order_by(Image.date_created.desc())
    ).scalars().all()

    image_data = []
    for image in patientImages:
        id = image.id
        date = image.date_created
        frontImage = image.image_front
        image_front64 = base64.b64encode(frontImage).decode('utf-8')

        backImage = image.image_back
        image_back64 = base64.b64encode(backImage).decode('utf-8')
        leftImage = image.image_left
        image_left64 = base64.b64encode(leftImage).decode('utf-8')
        rightImage = image.image_right
        image_right64 = base64.b64encode(rightImage).decode('utf-8')
        image_data.append({
            "id": id,
            "date": date,
            "frontImage": image_front64,
            "backImage": image_back64,
            "leftImage": image_left64,
            "rightImage": image_right64
        })

    return render_template("patientHome.html", data=image_data)


@app.route("/compareImages")
def compareImages():
    id1 = request.args.get('date1')
    print(id1)
    id2 = request.args.get('date2')
    print(id2)

    patient = request.args.get('patient')
    print(patient)

    # Ensure you use Image.id for the filter
    patientImages = db.session.execute(
        db.select(Image).filter(or_(Image.id == id1, Image.id == id2))
        .order_by(Image.date_created.desc())
    ).scalars().all()

    image_data = []
    for image in patientImages:
        date = image.date_created
        frontImage = image.image_front
        image_front64 = base64.b64encode(frontImage).decode('utf-8')

        backImage = image.image_back
        image_back64 = base64.b64encode(backImage).decode('utf-8')
        leftImage = image.image_left
        image_left64 = base64.b64encode(leftImage).decode('utf-8')
        rightImage = image.image_right
        image_right64 = base64.b64encode(rightImage).decode('utf-8')
        image_data.append({
            "id": image.id,  # Include ID for easy reference in frontend
            "date": date,
            "frontImage": image_front64,
            "backImage": image_back64,
            "leftImage": image_left64,
            "rightImage": image_right64
        })


    return render_template("compareImages.html", data=image_data)

@app.route("/enterNewPatient")
def enterNewPatient():
    return render_template("enterNewPatient.html")



@app.route("/getUser", methods=['POST'])
def getUser():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Fetch user by email
    user = User.query.filter_by(email=email).first()

    # Check if user exists and verify the password
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return jsonify({"message": "User authenticated successfully"}), 200

    # Return error if authentication fails
    return jsonify({"error": "Incorrect email or password"}), 401

    return jsonify({"message": "current user recieved"})

@app.route("/createUser", methods=['POST'])
def createUser():
    data = request.json
    email = data['email']
    password = data['password']
    name = data['name']
    print(email)
    print(password)

    nameTaken = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if nameTaken:
        return jsonify({"error":"email is taken"}),401
    addUser(name,email,password)

    return jsonify({"message": "new user recieved"})

@app.route("/createPatient", methods=['POST'])
def createPatient():
    data = request.json
    patientName = data['patient']
    print(patientName)
    nameTaken = db.session.execute(db.select(Patient).filter_by(user_id=current_user.id).filter_by(patient_name=patientName)).scalar_one_or_none()
    if nameTaken:
        return jsonify({"error":"name is taken"}),401


    addPatient(patientName,current_user.id)

    return jsonify({"message": "new user recieved"})



@app.route("/uploadImages", methods=['GET', 'POST'])
@login_required
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

            globalImages['imgFront'] = imgFront

        if fileBack:
            filenameBack = secure_filename(fileBack.filename)
            filepathBack = os.path.join(app.config['UPLOAD_FOLDER'], filenameBack)
            fileBack.save(filepathBack)
            imgBack = cv2.imread(filepathBack)
            if imgBack is None:
                return "Error: Unable to read uploaded back image."

            globalImages['imgBack'] = imgBack

        if fileLeft:
            filenameLeft = secure_filename(fileLeft.filename)
            filepathLeft = os.path.join(app.config['UPLOAD_FOLDER'], filenameLeft)
            fileLeft.save(filepathLeft)
            imgLeft = cv2.imread(filepathLeft)
            if imgLeft is None:
                return "Error: Unable to read uploaded left image."

            globalImages['imgLeft'] = imgLeft


        if fileRight:
            filenameRight = secure_filename(fileRight.filename)
            filepathRight = os.path.join(app.config['UPLOAD_FOLDER'], filenameRight)
            fileRight.save(filepathRight)
            imgRight = cv2.imread(filepathRight)
            if imgRight is None:
                return "Error: Unable to read uploaded right image."

            globalImages['imgRight'] = imgRight


    return render_template("uploadImages.html")
@app.route("/saveImages",methods=['POST'])
def saveImages():
    data = request.json
    patientName= data['patientData']
    print(patientName)
    patientID = db.session.execute(db.select(Patient.id).filter_by(patient_name=patientName)).scalar()
    print(patientID)
    if patientID:
        addImage(savedImages['front'],savedImages['back'],savedImages['left'],savedImages['right'],patientID)
        return jsonify({"message":"Successful Image Upload"})
    else:
        return jsonify({"error":"Unsuccessful Image upload"})




@app.route("/get_coordinatesFront", methods=['POST'])
def get_coordinatesFront():
    data = request.json
    x = data['xFront']
    y = data['yFront']
    width = data['width']
    height = data['height']


    img_copy = globalImages['imgFront'].copy()
    processed_image = drawCross(img_copy, x, y,width,height)
    savedImages["front"]= processed_image
    base64_image = image_to_base64(processed_image)


    return jsonify({"message": "Coordinates received successfully.", "image": base64_image})

@app.route("/uploadFront", methods=['POST'])
def uploadFront():
    data = request.json
    img_front_base64 = data['imgFront']
    globalImages['imgFront'] = base64_to_image(img_front_base64)
    savedImages['front']=globalImages['imgFront']

    return jsonify({"message": "Front image received successfully."})

@app.route("/get_coordinatesBack", methods=['POST'])
def get_coordinatesBack():
    data = request.json
    x = data['xBack']
    y = data['yBack']
    width = data['width']
    height = data['height']
    print(width)
    print(height)

    img_copy = globalImages['imgBack'].copy()
    processed_image = drawCross(img_copy, x, y, width, height)
    savedImages["back"]= processed_image
    base64_image = image_to_base64(processed_image)

    return jsonify({"message": "Coordinates received successfully.", "image": base64_image})

@app.route("/uploadBack", methods=['POST'])
def uploadBack():
    data = request.json
    img_back_base64 = data['imgBack']
    globalImages['imgBack'] = base64_to_image(img_back_base64)
    savedImages['back'] = globalImages['imgBack']

    return jsonify({"message": "Back image received successfully."})

@app.route("/get_coordinatesLeft", methods=['POST'])
def get_coordinatesLeft():
    data = request.json
    x = data['xLeft']
    y = data['yLeft']
    width = data['width']
    height = data['height']
    print(width)
    print(height)

    img_copy = globalImages['imgLeft'].copy()
    processed_image = drawCross(img_copy, x, y, width, height)
    savedImages["left"]= processed_image
    base64_image = image_to_base64(processed_image)

    return jsonify({"message": "Coordinates received successfully.", "image": base64_image})

@app.route("/uploadLeft", methods=['POST'])
def uploadLeft():
    data = request.json
    img_left_base64 = data['imgLeft']
    globalImages['imgLeft'] = base64_to_image(img_left_base64)
    savedImages['left'] = globalImages['imgLeft']

    return jsonify({"message": "Left image received successfully."})

@app.route("/get_coordinatesRight", methods=['POST'])
def get_coordinatesRight():
    data = request.json
    x = data['xRight']
    y = data['yRight']
    width = data['width']
    height = data['height']
    print(width)
    print(height)

    img_copy = globalImages['imgRight'].copy()

    processed_image = drawCross(img_copy, x, y, width, height)
    savedImages["right"]= processed_image
    base64_image = image_to_base64(processed_image)

    return jsonify({"message": "Coordinates received successfully.", "image": base64_image})

@app.route("/uploadRight", methods=['POST'])
def uploadRight():
    data = request.json
    img_right_base64 = data['imgRight']
    globalImages['imgRight'] = base64_to_image(img_right_base64)
    savedImages['right'] = globalImages['imgRight']

    return jsonify({"message": "Right image received successfully."})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

