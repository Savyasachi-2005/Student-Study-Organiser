# Keep your existing imports
from flask import Flask, render_template, flash, redirect, url_for,jsonify, session, request
from forms import LoginForm, RegisterForm, RequestResetForm, ResetPasswordForm, FeedbackForm
# --- Import Resource model ---
from models import db, User, Resource, ResourceURL
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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ABHISHEKHIREMATH04242005')
app.config['GOOGLE_ANALYTICS_ID'] = os.environ.get('GOOGLE_ANALYTICS_ID')

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    # Log database connection details (without password)
    db_info = database_url.split('@')
    if len(db_info) > 1:
        print(f"Connected to database at: {db_info[1]}")
else:
    print("Warning: DATABASE_URL not set, using default SQLite database")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'abhishekhiremath0424@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')  # This should be your App Password
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', 'abhishekhiremath0424@gmail.com')

# Initialize extensions
bcrypt = Bcrypt()
bcrypt.init_app(app)
mail.init_app(app)

db.init_app(app)
migrate.init_app(app, db)

# Initialize database
def init_db():
    with app.app_context():
        try:
            print("Attempting to connect to database...")
            print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

# Call init_db during application startup
init_db()

oauth = OAuth()
oauth.init_app(app)

# Check if OAuth credentials are set
if not os.environ.get('GOOGLE_CLIENT_ID') or not os.environ.get('GOOGLE_CLIENT_SECRET'):
    print("Warning: Google OAuth credentials not set. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.")

google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account',
        'response_type': 'code',
        'access_type': 'offline'
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

    # Load URLs for each resource
    for resource in user_resources:
        resource.resource_urls = ResourceURL.query.filter_by(resource_id=resource.id).all()

    # Fetch distinct subjects for the filter dropdown for this user
    subjects_query = db.session.query(Resource.subject)\
                               .filter(Resource.user_id == user_id)\
                               .distinct()\
                               .order_by(Resource.subject)\
                               .all()
    # Extract subject strings, handling potential None values
    subjects = [s[0] for s in subjects_query if s[0]]

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
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        urls = request.form.getlist('urls[]')
        primary_url_index = int(request.form.get('primary_url', 0))
        subject = request.form.get('subject')
        difficulty = request.form.get('difficulty')
        tags = request.form.get('tags')

        if not title or not urls:
            flash('Title and at least one URL are required fields.', 'danger')
            return render_template('add_resource.html')

        try:
            new_resource = Resource(
                title=title,
                description=description,
                subject=subject,
                difficulty=difficulty,
                tags=tags,
                user_id=session['user_id']
            )
            db.session.add(new_resource)
            db.session.flush()  # Get the resource ID without committing

            # Add URLs
            for i, url in enumerate(urls):
                resource_url = ResourceURL(
                    url=url,
                    is_primary=(i == primary_url_index),
                    resource_id=new_resource.id
                )
                db.session.add(resource_url)

            db.session.commit()
            flash('Resource added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding resource: {str(e)}', 'danger')
            return render_template('add_resource.html')

    return render_template('add_resource.html')

@app.route('/resource/<int:resource_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    
    # Check if the resource belongs to the current user
    if resource.user_id != session['user_id']:
        flash('You do not have permission to edit this resource.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        urls = request.form.getlist('urls[]')
        primary_url_index = int(request.form.get('primary_url', 0))
        subject = request.form.get('subject')
        difficulty = request.form.get('difficulty')
        tags = request.form.get('tags')

        if not title or not urls:
            flash('Title and at least one URL are required fields.', 'danger')
            return render_template('edit_resource.html', resource=resource)

        try:
            # Update basic resource info
            resource.title = title
            resource.description = description
            resource.subject = subject
            resource.difficulty = difficulty
            resource.tags = tags

            # Delete existing URLs
            ResourceURL.query.filter_by(resource_id=resource.id).delete()

            # Add new URLs
            for i, url in enumerate(urls):
                if url.strip():  # Only add non-empty URLs
                    resource_url = ResourceURL(
                        url=url.strip(),
                        is_primary=(i == primary_url_index),
                        resource_id=resource.id
                    )
                    db.session.add(resource_url)

            db.session.commit()
            flash('Resource updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating resource: {str(e)}', 'danger')
            return render_template('edit_resource.html', resource=resource)

    # For GET request, prepare the resource data
    resource_data = {
        'id': resource.id,
        'title': resource.title,
        'description': resource.description,
        'subject': resource.subject,
        'difficulty': resource.difficulty,
        'tags': resource.tags,
        'resource_urls': ResourceURL.query.filter_by(resource_id=resource.id).all()
    }
    
    return render_template('edit_resource.html', resource=resource_data)

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
    resources = Resource.query.filter_by(user_id=session['user_id']).all()
    
    # Calculate statistics
    total_resources = len(resources)
    completed_resources = sum(1 for r in resources if r.progress == 'completed')
    in_progress_resources = sum(1 for r in resources if r.progress == 'in-progress')
    
    # Prepare data for charts
    progress_data = []
    
    for resource in resources:
        # Get all URLs for this resource
        urls = ResourceURL.query.filter_by(resource_id=resource.id).all()
        primary_url = next((url.url for url in urls if url.is_primary), urls[0].url if urls else None)
        
        # Determine icon based on URL type
        icon = 'book'  # default icon
        if primary_url:
            if 'youtube.com' in primary_url or 'youtu.be' in primary_url:
                icon = 'youtube'
            elif 'pdf' in primary_url.lower():
                icon = 'file-pdf'
            elif 'github.com' in primary_url:
                icon = 'github'
            elif 'medium.com' in primary_url:
                icon = 'medium'
            elif 'udemy.com' in primary_url:
                icon = 'graduation-cap'
            elif 'coursera.org' in primary_url:
                icon = 'university'
        
        # Add to progress data
        progress_data.append({
            'id': resource.id,
            'title': resource.title,
            'url': primary_url,
            'progress': resource.progress or 'Not Started',
            'progress_percentage': resource.progress_percentage or 0,
            'last_updated': resource.last_updated,
            'subject': resource.subject or 'Uncategorized',
            'type': resource.type or 'General',
            'icon': icon,
            'notes': resource.notes if hasattr(resource, 'notes') else ''
        })
    
    # Sort progress_data by last_updated, handling None values
    progress_data.sort(key=lambda x: x['last_updated'] if x['last_updated'] is not None else datetime.min, reverse=True)
    
    return render_template('track_progress.html',
                         resources=resources,
                         progress_data=progress_data,
                         total_resources=total_resources,
                         completed_resources=completed_resources,
                         in_progress_resources=in_progress_resources)

@app.route('/update_progress', methods=['POST'])
@login_required
def update_progress():
    data = request.get_json()
    resource_id = data.get('resource_id')
    status = data.get('status')
    progress_percentage = int(data.get('progress_percentage', 0))
    notes = data.get('notes', '')
    
    resource = Resource.query.get_or_404(resource_id)
    
    # Verify resource belongs to user
    if resource.user_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        # Update status and progress percentage
        resource.progress = status
        resource.progress_percentage = progress_percentage
        
        # Update notes if provided
        if hasattr(resource, 'notes'):
            resource.notes = notes
        
        # Update last_updated timestamp
        resource.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        # Return updated resource data
        return jsonify({
            'success': True,
            'message': 'Progress updated successfully',
            'status': resource.progress,
            'progress_percentage': resource.progress_percentage,
            'notes': resource.notes if hasattr(resource, 'notes') else ''
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/chat_assistant')
@login_required
def chat_assistant():
    return render_template('chat_assistant.html')

@app.route('/login/google')
def login_google():
    try:
        # Get the base URL from environment variable or use the request's URL
        base_url = os.environ.get('RENDER_EXTERNAL_URL', request.url_root.rstrip('/'))
        redirect_uri = f"{base_url}/authorize/google"
        print(f"Redirect URI: {redirect_uri}")  # Debug log
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        print(f"Error in login_google: {e}")  # Debug log
        flash('Error initiating Google login. Please try again.', 'danger')
        return redirect(url_for('login'))

@app.route('/authorize/google')
def authorize_google():
    try:
        token = google.authorize_access_token()
        if not token:
            flash('Failed to get access token from Google.', 'danger')
            return redirect(url_for('login'))
            
        userinfo = google.get('https://www.googleapis.com/oauth2/v3/userinfo')
        if not userinfo:
            flash('Failed to get user information from Google.', 'danger')
            return redirect(url_for('login'))
            
        user_data = userinfo.json()
        email = user_data.get('email')
        
        if not email:
            flash('Email not provided by Google.', 'danger')
            return redirect(url_for('login'))
            
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user
            username = email.split('@')[0]
            user = User(
                username=username,
                email=email,
                password=''  # No password needed for OAuth users
            )
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully!', 'success')
        
        # Log the user in
        session['user_id'] = user.id
        session['username'] = user.username
        session['log_in'] = True
        
        flash('Login Successful', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        print(f"Error in authorize_google: {e}")  # Debug log
        flash('Error during Google authentication. Please try again.', 'danger')
        return redirect(url_for('login'))

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

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        try:
            if not app.config['MAIL_PASSWORD']:
                raise Exception("Email configuration is not properly set up. Please contact the administrator.")
                
            # Create email message
            msg = Message(
                f'New Website Feedback: {form.feedback_type.data}',
                sender=app.config['MAIL_USERNAME'],
                recipients=['abhishekhiremath0424@gmail.com']
            )
            
            # Format email body
            feedback_type_map = {
                'bug': 'Bug Report',
                'suggestion': 'Feature Suggestion',
                'improvement': 'Improvement Idea',
                'other': 'Other Feedback'
            }
            
            msg.body = f'''
            New Website Feedback Received:
            
            Type: {feedback_type_map.get(form.feedback_type.data, 'Other')}
            Name: {form.name.data}
            Email: {form.email.data}
            Message: {form.message.data}
            
            Contact Information:
            - Email: abhishekhiremath0424@gmail.com
            - WhatsApp: +91 8147893200
            
            Technical Details:
            Sent from: {request.remote_addr}
            User Agent: {request.user_agent}
            '''
            
            # Send email
            mail.send(msg)
            flash('Thank you for your feedback! We will review it and get back to you if needed.', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            print(f"Error sending feedback email: {e}")
            error_message = str(e)
            if "Authentication Required" in error_message:
                flash('Email service is currently unavailable. Please try again later or contact us directly.', 'danger')
            else:
                flash('There was an error sending your feedback. Please try again later or contact us directly.', 'danger')
    
    return render_template('feedback.html', form=form)

if __name__ == '__main__':
    app.run(debug=True, port=5000) # Running on port 5000