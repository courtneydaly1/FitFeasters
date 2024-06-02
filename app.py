import os, requests
from flask import Flask, request, render_template, redirect, flash, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.exceptions import Unauthorized
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from forms import SignUpForm, LoginForm, DeleteForm, SearchForm, UserEditForm
from models import db, connect_db, User, Recipes



CURR_USER_KEY = "curr_user"
API_KEY = '43cb4f5704da4cfe9d4d261fbb40c746'
BASE_URL = 'https://api.spoonacular.com/recipes/complexSearch'

app = Flask(__name__)

# Configuration

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://default:XDtSO0Ma3rpv@ep-yellow-boat-a4lryrfg.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'food4thesoul')


# Debug toolbar
debug = DebugToolbarExtension(app)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Database setup
connect_db(app)
app.app_context().push()
db.create_all()

#################################### User Sign up/login/logout

@app.before_request
def add_user_to_g():
    """If we're logged in, add current user to Flask global."""
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

def do_login(user):
    """Log in user."""
    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout user."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route("/")
def homepage():
    """Homepage of site; redirect to register."""
    return render_template("/users/homepage.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user signup."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

    form = SignUpForm()

    if form.validate_on_submit():
        try:
            username = form.username.data
            password = form.password.data
            first_name = form.first_name.data
            last_name = form.last_name.data
            email = form.email.data
            image_url = form.image_url.data

            user = User.signup(username, password, first_name, last_name, email, image_url)
            db.session.commit()
            
        except IntegrityError as e:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)
        return redirect("/search_form")

    else:
        return render_template("users/signup.html", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Produce login form or handle login."""
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/search_form")
        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)

@app.route("/logout")
def logout():
    """Logout route."""
    session.pop(CURR_USER_KEY)
    flash("You have been logged out.", "success")
    return redirect("/login")

############################ General User routes

@app.route("/users/<username>")
def show_user(username):
    """Example page for logged-in-users."""

    if CURR_USER_KEY not in session or str(username) != str(session[CURR_USER_KEY]):
        raise Unauthorized()
    
    user = User.query.get(username)
    form = DeleteForm()
    return render_template("/users/homepage.html", user=user, form=form)


   
@app.route('/users/edit_user', methods=['GET', 'POST'])
def edit_user():
    """Update profile for current user."""
    
    if CURR_USER_KEY not in session:
        return redirect('/login')
    
    user = User.query.get(session.get(CURR_USER_KEY))
    form = UserEditForm(obj=user)
    
    if form.validate_on_submit():
            user.username = form.username.data
            user.email = form.email.data
            if form.password.data:
                # Hash the new password before storing it
                hashed_password = generate_password_hash(form.password.data)
                user.password = hashed_password
            
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect('/search_form')
    
    return render_template('users/edit_user.html', form=form, user=user)


@app.route("/users/<username>/delete", methods=["POST"])
def remove_user(username):
    """Remove user and redirect to login."""
    if "username" not in session or username != session['username']:
        raise Unauthorized()

    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop("username")
    return redirect("/login")

##################### Recipe searches

@app.route('/search_form', methods=['GET', 'POST'])
def search_form():
    """Render the search form template."""
    form = SearchForm()
    return render_template('/users/search_form.html', form=form)

@app.route('/search', methods=['POST'])
def search():
    """Handle recipe search."""
    form = SearchForm()
    if form.validate_on_submit():
        title = form.title.data
        intolerances = form.intolerances.data
        includeIngredients = form.includeIngredients.data
        
        query = f'{title}&intolerances={intolerances}&includeIngredients={includeIngredients}'
        endpoint = f'https://api.spoonacular.com/recipes/complexSearch?apiKey={API_KEY}&number=6&query={query}'
        response = requests.get(endpoint)
      
        if response.status_code == 200:
            data = response.json()
        
        # Save fetched recipes to the database and display results
        for recipe_data in data['results']:
            recipe = Recipes(
                recipe_id= recipe_data['id'],
                title=recipe_data['title'],
                image_url=recipe_data['image']
                
            )
            db.session.add(recipe)
            db.session.commit()
        
        return render_template('/users/search_results.html', recipes=data['results'])
    else:
        return 'Failed to fetch data from Spoonacular API', 500

    return render_template('/users/search_form.html', form=form)
    

@app.route('/search_food', methods=["POST"])
def general_search():
    """Handle general searches"""
   
    # print(request.args.get('query'))
    # query=request.args.get('query')
    query= request.form.get('query')
    endpoint = f'https://api.spoonacular.com/recipes/complexSearch?apiKey={API_KEY}&number=6&query={query}'
    response = requests.get(endpoint)
    
    if response.status_code == 200:
        data = response.json()
        
        # Save fetched recipes to the database and display results
        for recipe_data in data['results']:
            recipe = Recipes(
                recipe_id= recipe_data['id'],
                title=recipe_data['title'],
                image_url=recipe_data['image']
                
            )
            db.session.add(recipe)
            db.session.commit()
            
        return render_template('/users/search_results.html', recipes=data['results'])
    else:
        return 'Failed to fetch data from Spoonacular API', 500

    return render_template('/users/search_form.html', form=form)


@app.route('/recipe_details/<int:recipe_id>')
def recipe_details(recipe_id):
    """Handle request for fetching details of a recipe"""
    endpoint = f'https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={API_KEY}'
    response = requests.get(endpoint)
    
    if response.status_code == 200:
        recipe_details = response.json()
        

        return render_template('/users/recipe_details.html', recipe=recipe_details)
    else:
        return 'Failed to fetch recipe details from Spoonacular API', 500


########################Future Functionality ##########################################

# @app.route('/users/<username>/my_recipes.html')
# def show_my_recipes(username):
#     if CURR_USER_KEY not in session:
#         raise Unauthorized()
    
#     user = User.query.get(username)
#     form = DeleteForm()
    
#     return render_template('/users/my_recipes.html', user=user)
