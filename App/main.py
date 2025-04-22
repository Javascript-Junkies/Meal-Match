from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from models import db
from models.user import User
from models.recipe import Recipe
from models.ingredient import Ingredient, Inventory
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change for production

# Config
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
db.init_app(app)
migrate = Migrate(app, db)

# ----------------------------------
# Authentication
# ----------------------------------
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        flash('Login successful!')
    else:
        flash('Invalid credentials')
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.')
    return redirect('/')

# Helper
def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@app.context_processor
def inject_user():
    return dict(is_authenticated=('user_id' in session), current_user=current_user())

# ----------------------------------
# Pages
# ----------------------------------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add-recipe', methods=['GET', 'POST'])
def add_recipe():
    if request.method == 'POST':
        name = request.form['name']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']

        new_recipe = Recipe(
            name=name,
            ingredients=ingredients,
            instructions=instructions
        )
        db.session.add(new_recipe)
        db.session.commit()
        flash("Recipe added successfully!")
        return redirect('/')

    return render_template('add_recipe.html')

@app.route('/recipe/<int:id>')
def recipe_detail(id):
    recipe = Recipe.query.get_or_404(id)
    return render_template('recipe_detail.html', recipe=recipe)

@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    user = current_user()
    if not user:
        flash("Please login first")
        return redirect('/')

    if request.method == 'POST':
        name = request.form['name']
        if request.form['action'] == 'add':
            ingredient = Ingredient.query.filter_by(name=name).first()
            if not ingredient:
                ingredient = Ingredient(name=name)
                db.session.add(ingredient)
                db.session.commit()

            inventory_item = Inventory(user_id=user.id, ingredient_id=ingredient.id)
            db.session.add(inventory_item)
            db.session.commit()
            flash(f"Added {name} to inventory")

        elif request.form['action'] == 'remove':
            ingredient = Ingredient.query.filter_by(name=name).first()
            if ingredient:
                Inventory.query.filter_by(user_id=user.id, ingredient_id=ingredient.id).delete()
                db.session.commit()
                flash(f"Removed {name} from inventory")

    user_inventory = Inventory.query.filter_by(user_id=user.id).all()
    ingredient_names = [inv.ingredient.name for inv in user_inventory]
    return render_template('inventory.html', inventory=ingredient_names)

@app.route('/my-recipes')
def my_recipes():
    user = current_user()
    if not user:
        flash("Please login to view this page")
        return redirect('/')

    all_recipes = Recipe.query.all()
    user_ingredients = [inv.ingredient.name.lower() for inv in Inventory.query.filter_by(user_id=user.id).all()]

    recipes_info = []
    for recipe in all_recipes:
        recipe_ingredients = [i.strip().lower() for i in recipe.ingredients.split(',')]
        missing = [i for i in recipe_ingredients if i not in user_ingredients]
        recipes_info.append({
            'recipe': recipe,
            'missing': missing
        })

    return render_template('my_recipes.html', recipes_info=recipes_info)

if __name__ == '__main__':
    app.run(debug=True)
