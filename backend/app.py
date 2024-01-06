import datetime 
import json,time,os
from functools import wraps
from flask import Flask, jsonify, request, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
from sqlalchemy.orm import class_mapper
from werkzeug.utils import secure_filename
import jwt
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required


app = Flask(__name__)
app.secret_key = 'secret_secret_key'

#* SQLAlchemy configuration
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://user1:123@server/restaurant?driver=SQL+Server'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:123@localhost/restaurant'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Get the directory where app.py is located
app_directory = os.path.dirname(__file__)
app.config['UPLOAD_FOLDER'] = '/uploads'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.String(200))
    cooking_time = db.Column(db.String(100))
    image_path = db.Column(db.String(255))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()
#---------------------------------------------------------

#* Declaring login access 

# Generate a JWT
def generate_token(user_id):
    expiration = int(time.time()) + 3600  # Set the expiration time to 1 hour from the current time
    payload = {'user_id': user_id, 'exp': expiration}
    token = jwt.encode(payload, 'secret-secret-key', algorithm='HS256')
    return token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(current_user_id, *args, **kwargs)

    return decorated

def model_to_dict(model):
    serialized_model = {}
    for key in model.__mapper__.c.keys():
        serialized_model[key] = getattr(model, key)
    return serialized_model


# opening cors to everyone for tests
CORS(app)

#image uploads
@app.route('/uploads/<filename>', methods=['GET'])
def get_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

#display recipes in client
@app.route('/get_recipes', methods=['GET'])
def get_recipes():
    recipes = db.session.query(Recipe).all()
    recipes_json = []  

    for recipe in recipes:
        recipe_json = {  
            'id':recipe.id,
            'name': recipe.name,
            'ingredients': recipe.ingredients,
            'cooking_time': recipe.cooking_time,
            'image_url': url_for('get_image', filename=recipe.image_path)  # Corrected variable name
        }
        recipes_json.append(recipe_json)
    # print (recipe_json)

    return jsonify({'recipes': recipes_json})

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    if request.method == 'POST':
        name = request.form['name']
        ingredients = request.form['ingredients']
        cooking_time = request.form['cookingTime']

        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and allowed_file(image_file.filename):
                # Generate a secure filename and save the image
                filename = secure_filename(image_file.filename)

                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)

                new_recipe = Recipe(
                    name=name, 
                    ingredients=ingredients, 
                    cooking_time=cooking_time, 
                    image_path=filename
                )
                db.session.add(new_recipe)
                db.session.commit()
                return jsonify({'message': 'added recipe successfully'})

        return jsonify({'message': 'problem with adding'})

@app.route('/delete_recipe/<int:id>', methods=['DELETE'])
def delete_recipe(id):
    if request.method == 'DELETE':
        recipe_to_delete = db.session.query(Recipe).filter_by(id=id).first()

        if recipe_to_delete:
            db.session.delete(recipe_to_delete)
            db.session.commit()
            return {"message":"Recipe deleted successfully"}
        else:
            return {"message":"Recipe not found"}

@app.route('/update_recipe', methods=['PUT'])
def update_recipe():
    if request.method == 'PUT':
        id = request.form['id']
        recipe_to_edit = db.session.query(Recipe).filter_by(id=id).first()
        name = request.form['name']
        ingredients = request.form['ingredients']
        cooking_time = request.form['cookingTime']
        print(id,name,ingredients,cooking_time)

        if recipe_to_edit:
            
            recipe_to_edit.name = name
            recipe_to_edit.ingredients = ingredients
            recipe_to_edit.cooking_time = cooking_time
            db.session.commit()
            return {"message":"Recipe edited successfully"}
        else:
            return {"message":"Recipe not found"}

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Check if the user exists
    user = User.query.filter_by(username=username).first()

    if user and bcrypt.check_password_hash(user.password, password):
        # Generate an access token with an expiration time
        expires = datetime.timedelta(hours=1)
        access_token = create_access_token(identity=user.id, expires_delta=expires)
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401



@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    # Check if the username is already taken
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'Username is already taken'}), 400

    # Hash and salt the password using Bcrypt
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create a new user and add to the database
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

@app.route('/protected', methods=['GET'])
@jwt_required()  # Use this decorator to protect routes
def protected_route():
    current_user_id = get_jwt_identity()
    return jsonify({'message': f'Hello, User {current_user_id}!'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
