# Keep your existing imports
from flask import Flask, render_template, flash, redirect, url_for,jsonify, session, request
from forms import LoginForm, RegisterForm, RequestResetForm, ResetPasswordForm
# --- Import Resource model ---
from models import db, User, Resource
from flask_bcrypt import Bcrypt
from functools import wraps
from flask_migrate import Migrate
# --- Import datetime for Resource timestamp ---
from datetime import datetime
from sqlalchemy import case  # Add this import for the case function
from authlib.integrations.flask_client import OAuth
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
import os
migrate = Migrate()
mail = Mail()

# Initialize Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ABHISHEKHIREMATH')

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'postgresql://postgres:12345@localhost:5432/flask_auth_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

# Initialize extensions
bcrypt = Bcrypt()
bcrypt.init_app(app)
mail.init_app(app)

db.init_app(app)
migrate.init_app(app, db) # Initialize migration with app and db

# Move db.create_all() inside app context
with app.app_context():
    try:
        db.create_all() # Creates User and Resource tables if they don't exist
    except Exception as e:
        print(f"Error creating database tables: {e}")

oauth = OAuth()
oauth.init_app(app)
google=oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid profile email',
        'response_type': 'code'
    }
)

# Initialize serializer for password reset tokens
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    # Remove the automatic redirect to dashboard
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            session['username'] = user.username # Store username in session
            session['log_in'] = True # Optional: Store login time
            flash('Login Successful', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if email or username already exists
        existing_user_email = User.query.filter_by(email=form.email.data).first()
        existing_user_username = User.query.filter_by(username=form.username.data).first()
        if existing_user_email:
            flash('Email address already registered.', 'danger')
        elif existing_user_username:
             flash('Username already taken.', 'danger')
        else:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=hashed_password
            )
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You can now log in', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

# --- UPDATED DASHBOARD ROUTE ---
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    # Query resources belonging to the user, order by most recently added
    user_resources = Resource.query.filter_by(user_id=user_id)\
                                   .order_by(Resource.date_added.desc())\
                                   .all()

    # Fetch distinct subjects for the filter dropdown for this user
    subjects_query = db.session.query(Resource.subject)\
                               .filter(Resource.user_id == user_id)\
                               .distinct()\
                               .order_by(Resource.subject)\
                               .all()
    # Extract subject strings, handling potential None values
    subjects = [s[0] for s in subjects_query if s[0]]

    # Pass the resources and subjects to the template
    # The template uses session['username'], so no need to pass it separately
    return render_template('dashboard.html', resources=user_resources, subjects=subjects)
# --- END UPDATED DASHBOARD ROUTE ---

@app.route('/logout',methods=['GET','POST'])
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('username', None) # Also remove username
    flash('You have been logged out.', 'success')
    return redirect(url_for('login')) # Redirect to login after logout usually

@app.route('/categories') # Removed methods=['GET'] as GET is default
@login_required
def categories():
    user_id = session['user_id']

    # --- Fetch ALL resources for potential filtering ---
    # We might filter later with JS or modify this query for server-side filtering
    user_resources = Resource.query.filter_by(user_id=user_id)\
                                   .order_by(Resource.date_added.desc())\
                                   .all()

    # --- Fetch distinct values for filters ---
    subjects_query = db.session.query(Resource.subject)\
                               .filter(Resource.user_id == user_id, Resource.subject.isnot(None), Resource.subject != '')\
                               .distinct()\
                               .order_by(Resource.subject)\
                               .all()
    subjects = [s[0] for s in subjects_query]

    difficulties_query = db.session.query(Resource.difficulty)\
                                 .filter(Resource.user_id == user_id, Resource.difficulty.isnot(None), Resource.difficulty != '')\
                                 .distinct()\
                                 .order_by(Resource.difficulty)\
                                 .all()
    difficulties = [d[0] for d in difficulties_query]

    # --- Fetch distinct tags (more complex as they are comma-separated) ---
    # Option 1: Get all tags, process in Python (simpler for moderate data)
    all_tags_list = []
    for resource in user_resources:
        all_tags_list.extend(resource.get_tags_list()) # Uses the helper method from models.py
    # Get unique tags and sort them
    distinct_tags = sorted(list(set(all_tags_list)))

    # Option 2: Database-specific query (more efficient for large data, depends on DB)
    # Example for PostgreSQL using unnest:
    # tags_query = db.session.query(func.unnest(func.string_to_array(Resource.tags, ','))).distinct().all()
    # distinct_tags = sorted([tag[0].strip() for tag in tags_query if tag[0] and tag[0].strip()])

    return render_template(
        'categorize.html',
        resources=user_resources,
        subjects=subjects,
        difficulties=difficulties,
        tags=distinct_tags # Pass the unique tags list
    )
@app.route('/add_resource', methods=['GET', 'POST'])
@login_required
def add_resource():
    # form = ResourceForm() # Uncomment if using WTForms
    # if form.validate_on_submit(): # Uncomment if using WTForms
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        url = request.form.get('url')
        subject = request.form.get('subject')
        difficulty = request.form.get('difficulty')
        tags = request.form.get('tags') # Stored as comma-separated string

        if not title or not url:
            flash('Title and URL are required fields.', 'danger')
            # return render_template('add_resource.html', form=form) # If using WTForms
            return render_template('add_resource.html') # Re-render form on error

        try:
            new_resource = Resource(
                title=title,
                description=description,
                url=url,
                subject=subject if subject else None, # Handle empty string for subject
                difficulty=difficulty if difficulty else None, # Handle empty string
                tags=tags if tags else None, # Handle empty string
                user_id=session['user_id'] # Associate with logged-in user
                # 'completed' defaults to False, 'date_added' defaults to now
            )
            db.session.add(new_resource)
            db.session.commit()
            flash('Resource added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback() # Rollback in case of error
            flash(f'Error adding resource: {e}', 'danger')
            # Optionally log the error: app.logger.error(f"Error adding resource: {e}")

    # For a GET request, display the form
    # return render_template('add_resource.html', form=form) # If using WTForms
    return render_template('add_resource.html')
# --- END UPDATED ADD_RESOURCE ROUTE ---

# --- Add routes for Edit, Delete, Toggle Completion (Placeholders) ---

@app.route('/resource/<int:resource_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    # Check if the logged-in user is the author of the resource
    if resource.author.id != session['user_id']:
         flash('You do not have permission to edit this resource.', 'danger')
         return redirect(url_for('dashboard'))

    # form = ResourceForm(obj=resource) # Example if using WTForms
    if request.method == 'POST':
         # --- Update resource logic ---
         resource.title = request.form.get('title')
         resource.description = request.form.get('description')
         resource.url = request.form.get('url')
         resource.subject = request.form.get('subject')
         resource.difficulty = request.form.get('difficulty')
         resource.tags = request.form.get('tags')
         # Add validation as needed
         try:
             db.session.commit()
             flash('Resource updated successfully!', 'success')
             return redirect(url_for('dashboard'))
         except Exception as e:
             db.session.rollback()
             flash(f'Error updating resource: {e}', 'danger')
         # return render_template('edit_resource.html', form=form, resource=resource) # If using WTForms
         return render_template('edit_resource.html', resource=resource)

    # --- For GET request ---
    # return render_template('edit_resource.html', form=form, resource=resource) # If using WTForms
    return render_template('edit_resource.html', resource=resource) # Need an edit_resource.html template

@app.route('/resource/<int:resource_id>/mark_completed', methods=['POST'])
@login_required
def mark_resource_completed(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if resource.author.id != session['user_id']:
        return jsonify({'success': False, 'message': 'Permission denied.'}), 403 # Forbidden

    try:
        resource.progress = 'Completed' # Update the progress status
        db.session.commit()
        # Flash messages won't be seen with fetch, so JSON is better
        # flash('Resource marked as completed!', 'success')
        return jsonify({'success': True, 'message': 'Resource marked as completed!'})
    except Exception as e:
        db.session.rollback()
        # flash(f'Error marking resource as completed: {e}', 'danger')
        print(f"Error marking completed: {e}") # Log error for debugging
        return jsonify({'success': False, 'message': f'Error: {e}'}), 500 # Internal Server Error
@app.route('/resource/<int:resource_id>/delete', methods=['POST'])
@login_required
def delete_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if resource.user_id != session['user_id']:
        return jsonify({
            'success': False, 
            'message': 'You do not have permission to delete this resource.'
        }), 403
    
    try:
        # Store resource title for success message
        resource_title = resource.title
        
        # Delete the resource
        db.session.delete(resource)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Resource "{resource_title}" deleted successfully!'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting resource: {e}")
        return jsonify({
            'success': False, 
            'message': 'An error occurred while deleting the resource. Please try again.'
        }), 500

   
@app.route('/track_progress')
@login_required
def track_progress():
    user_id = session['user_id']
    
    # Get all resources for the user
    resources = Resource.query.filter_by(user_id=user_id).all()
    
    # Format resources for JavaScript
    resources_data = []
    for resource in resources:
        resources_data.append({
            'id': resource.id,
            'title': resource.title,
            'description': resource.description,
            'subject': resource.subject or 'Uncategorized',
            'type': resource.type or 'Link',
            'status': 'Completed' if resource.progress_percentage == 100 else 'In Progress' if resource.progress_percentage > 0 else 'Not Started',
            'progress': resource.progress_percentage,
            'last_studied': resource.last_updated.strftime("%Y-%m-%d") if resource.last_updated else "Never",
            'url': resource.url,
            'icon': 'book',  # Default icon, you can customize based on type
            'notes': resource.notes if hasattr(resource, 'notes') else ''  # Add notes if they exist
        })
    
    return render_template('track_progress.html',
                         resources=resources_data)

@app.route('/update_progress', methods=['POST'])
@login_required
def update_progress():
    data = request.get_json()
    resource_id = data.get('resource_id')
    progress = int(data.get('progress', 0))
    status = data.get('status')
    notes = data.get('notes', '')
    
    resource = Resource.query.get_or_404(resource_id)
    
    # Verify resource belongs to user
    if resource.user_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        # Update progress percentage
        resource.progress_percentage = progress
        
        # Update status based on progress
        if progress == 100:
            resource.progress = 'Completed'
        elif progress > 0:
            resource.progress = 'In Progress'
        else:
            resource.progress = 'Not Started'
        
        # Update notes if provided
        if hasattr(resource, 'notes'):
            resource.notes = notes
        
        # Update last_updated timestamp
        resource.last_updated = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Progress updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/chat_assistant')
@login_required
def chat_assistant():
    return render_template('chat_assistant.html')

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize/google')
def authorize_google():
    token = google.authorize_access_token()
    userinfo = google.get('https://www.googleapis.com/oauth2/v3/userinfo')
    
    # Check if user exists
    user = User.query.filter_by(email=userinfo.json()['email']).first()
    
    if not user:
        # Create new user
        user = User(
            username=userinfo.json()['email'].split('@')[0],  # Use email prefix as username
            email=userinfo.json()['email'],
            password=''  # No password needed for OAuth users
        )
        db.session.add(user)
        db.session.commit()
    
    # Log the user in
    session['user_id'] = user.id
    session['username'] = user.username
    session['log_in'] = True
    
    flash('Login Successful', 'success')
    return redirect(url_for('dashboard'))

@app.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    print("Forgot password route accessed")  # Debug line
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    form = RequestResetForm()
    print(f"Form submitted: {form.is_submitted()}")
    print(f"Form data: {form.data}")
    
    if request.method == 'POST':
        print("POST request received")  # Debug line
        if form.validate_on_submit():
            print("Form validated successfully")  # Debug line
            email = form.email.data
            user = User.query.filter_by(email=email).first()
            
            if user:
                print(f"User found: {user.email}")  # Debug line
                try:
                    send_reset_email(user)
                    flash('An email has been sent with instructions to reset your password.', 'info')
                    return redirect(url_for('login'))
                except Exception as e:
                    print(f"Error sending email: {str(e)}")  # Debug line
                    flash('An error occurred while sending the reset email. Please try again.', 'danger')
            else:
                flash('No account found with that email address.', 'warning')
    
    return render_template('forgot_password.html', form=form)

def send_reset_email(user):
    try:
        token = serializer.dumps(user.email, salt='password-reset-salt')
        msg = Message('Password Reset Request',
                     sender=app.config['MAIL_USERNAME'],
                     recipients=[user.email])
        msg.body = f'''To reset your password, visit the following link:
{url_for('reset_password', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
        print(f"Attempting to send email to: {user.email}")
        print(f"Using SMTP server: {app.config['MAIL_SERVER']}")
        print(f"Using port: {app.config['MAIL_PORT']}")
        mail.send(msg)
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('password_reset'))
    user = User.query.filter_by(email=email).first()
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

if __name__ == '__main__':
    app.run(debug=True, port=5000) # Running on port 5000