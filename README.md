# 📚 Study Resource Organizer

A comprehensive web application designed to help students **centralize, organize, and monitor** their learning resources in one intuitive platform. Perfect for self-paced learners juggling multiple content formats—videos, articles, courses, and personal notes—this app transforms scattered learning materials into a **structured, trackable study system**.

🚀 **Live Demo**: [StudyResourceOrganizer.app](https://student-study-organiser.onrender.com/)

## 🔍 Overview

The Study Resource Organizer solves a common challenge for modern learners: managing the overwhelming volume of digital learning materials across platforms. By providing a centralized system for resource tracking and organization, it helps users maintain focus, measure progress, and complete their learning goals efficiently.

## 🔧 Technology Stack

### Backend Architecture
- **Core Framework**: [Flask 3.0.0](https://flask.palletsprojects.com/) - Python-based web framework
- **Database**: 
  - PostgreSQL (production environment)
  - SQLite (development environment)
- **ORM & Migration**: SQLAlchemy with Flask-Migrate
- **Security**: 
  - Flask-Bcrypt for password hashing
  - Flask-WTF for CSRF protection
  - Authlib for OAuth integration
- **Communication**: 
  - Flask-Mail for email services
- **Deployment**: 
  - Gunicorn as WSGI server

### Frontend Components
- **Template Engine**: Jinja2
- **UI Framework**: Bootstrap 5
- **Languages**: HTML5, CSS3, JavaScript
- **Responsiveness**: Mobile-first design approach

### Deployment Infrastructure
- **Hosting**: Render.com (configured via `render.yaml`)
- **Environment Management**: Secure variable storage
- **Database**: Managed PostgreSQL instance
- **Scaling**: Auto-scaling configuration

## ✨ Key Features

### 🔐 User Authentication System
- **Multiple Login Methods**: 
  - Email/password registration and login
  - Google OAuth integration
- **Security Features**:
  - Bcrypt password hashing
  - Secure session management
  - CSRF protection
- **Account Management**:
  - Password reset functionality
  - Email verification
  - Profile customization

### 📁 Resource Management
- **Resource Addition**: Add URLs or upload files as study resources
- **Resource Types**: Support for videos, articles, PDFs, courses, and notes
- **Metadata Support**: 
  - Subject/topic categorization
  - Difficulty rating (Beginner, Intermediate, Advanced)
  - Custom tagging system
  - Priority labeling
  - Estimated completion time

### 📊 Progress Tracking
- **Status Management**: Track resources as Not Started, In Progress, or Completed
- **Progress Visualization**: 
  - Subject-level completion percentages
  - Overall learning journey visualization
  - Time-based progress tracking
- **Activity History**: Timestamp-based activity log

### 🧭 Dashboard & Navigation
- **Personalized Dashboard**: At-a-glance view of study progress and priorities
- **Advanced Filtering**: 
  - Multi-parameter search functionality
  - Filter by subject, status, tags, difficulty, and more
- **Custom Views**: Create and save personalized resource views
- **Quick Access**: Recently viewed resources section

### 💬 AI-Powered Study Assistant
- **Learning Support**: 
  - Contextual study tips and strategies
  - Resource recommendations based on user patterns
  - Motivation reminders and study streak tracking
- **Resource Analysis**: 
  - Automated difficulty estimation
  - Study time suggestions
  - Content summarization capabilities

### 📱 Additional Features
- **Responsive Design**: Seamless experience across devices
- **Feedback System**: User-driven feature suggestions
- **Notifications**: Email updates for progress milestones and reminders
- **Analytics**: Study pattern insights and optimization suggestions

## 🔐 Security Implementation

- **Authentication Security**:
  - Bcrypt password hashing with appropriate salt rounds
  - Time-safe comparison for sensitive operations
  - Rate limiting on authentication attempts
- **Data Protection**:
  - CSRF tokens for all state-changing operations
  - Input sanitization and validation
  - Parameterized database queries
- **Infrastructure Security**:
  - Environment-based configuration
  - Secure credential storage
  - HTTPS enforcement

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+
- PostgreSQL (production) or SQLite (development)
- pip and virtualenv

### Local Development Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/study-resource-organizer.git
cd study-resource-organizer

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (create a .env file)
# Example .env content:
# FLASK_APP=run.py
# FLASK_ENV=development
# SECRET_KEY=your_secure_random_key
# DATABASE_URL=sqlite:///site.db
# MAIL_SERVER=smtp.example.com
# MAIL_PORT=587
# MAIL_USE_TLS=True
# MAIL_USERNAME=your_email@example.com
# MAIL_PASSWORD=your_email_password
# GOOGLE_CLIENT_ID=your_google_client_id
# GOOGLE_CLIENT_SECRET=your_google_client_secret

# Initialize the database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run the development server
flask run
```

### Production Deployment
```bash
# Set production environment variables accordingly
# Deploy to Render.com using the render.yaml configuration
# Or follow your preferred hosting provider's instructions
```

## 📝 API Documentation

The application provides a RESTful API for programmatic resource management:

- `GET /api/resources` - List all resources
- `POST /api/resources` - Create a new resource
- `GET /api/resources/{id}` - Retrieve a specific resource
- `PUT /api/resources/{id}` - Update a resource
- `DELETE /api/resources/{id}` - Delete a resource

Detailed API documentation is available at `/api/docs` when running the application.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

- **Project Repository**: [https://github.com/yourusername/study-resource-organizer](https://github.com/Savyasachi-2005/Student-Study-Organiser)
- **Developer**: Abhishek Hiremath
- **Email**: abhishekhiremath0424@gmail.com
- **LinkedIn**: [Your LinkedIn Profile](https://www.linkedin.com/in/abhishek-hiremath-3020692a3/)

## 🙏 Acknowledgements

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Bootstrap](https://getbootstrap.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- All contributors and testers who have helped shape this project
