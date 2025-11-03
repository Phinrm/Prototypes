📝 Django Blogging Platform

A modern multi-author blogging application built with Django.
It supports secure authentication, responsive design, and a full author workflow — from writing to publishing and analytics.

📖 Overview

This platform allows multiple users to register, log in, and publish blog posts in a shared environment.
Each author manages their own posts privately in the admin and dashboard while posts are publicly visible on the homepage after publication.

🚀 Features
Core Features

Multi-user blogging with per-author restrictions

Public homepage with featured, recent, and popular posts

Category and tag-based browsing

Like and view tracking for engagement analytics

Commenting system on individual posts

Author and Admin Tools

Author Dashboard displaying:

Total posts, likes, views, and comments

Per-post statistics

Quick access to edit or delete their own posts

Admin can approve authors, manage categories, tags, and comments

Authentication

Secure login, signup, and logout

“Write a Post” button redirects unauthenticated users to login or signup

Only approved authors can publish posts

Frontend

Responsive navigation bar with a three-bar toggle for mobile screens

Search bar for quick content discovery

Clean layout with post thumbnails, excerpts, and “Read more” buttons

🧩 Tech Stack
Layer	Technology
Backend Framework	Django 5
Frontend	HTML5, CSS3, JavaScript
Database	SQLite (default) / PostgreSQL (production recommended)
Authentication	Django built-in auth
Deployment	Gunicorn + Nginx (recommended)
⚙️ Installation and Setup
1. Clone the Repository
git clone https://github.com/yourusername/myblog.git
cd myblog

2. Create and Activate Virtual Environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

3. Install Dependencies
pip install -r requirements.txt

4. Apply Migrations
python manage.py makemigrations
python manage.py migrate

5. Create a Superuser
python manage.py createsuperuser

6. Run the Development Server
python manage.py runserver


Visit the app at:
👉 http://127.0.0.1:8000/

🗂️ Project Structure
Myblog/
│
├── blogs/
│   ├── admin.py          # Custom admin interface
│   ├── models.py         # Post, Category, Tag, Comment, etc.
│   ├── views.py          # Core application logic
│   ├── forms.py          # Post and Comment forms
│   ├── urls.py           # App-specific URL routes
│   ├── templates/blog/   # HTML templates
│   └── static/blog/      # CSS, JS, and images
│
├── Myblog/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── manage.py
└── requirements.txt

🔒 Permissions and Author Flow
Role	Access
Superuser	Full control of posts, authors, categories, and tags
Author	Can create, update, and delete only their own posts
Visitor	Can view, like, and comment on posts
📊 Analytics

Each post tracks:

Total views (PostView)

Total likes (PostLike)

Total comments

These are displayed in the Author Dashboard for personal insights.

📱 Responsive Design

Mobile navigation menu transforms into a collapsible three-bar icon

Clean, readable typography for all devices

Sidebar widgets for categories, trending posts, and search

🧾 Deployment Checklist

Before deploying:

Run python manage.py collectstatic

Set DEBUG=False in settings.py

Add your domain to ALLOWED_HOSTS

Configure database (PostgreSQL recommended)

Use Gunicorn + Nginx for production

Enable HTTPS with SSL certificates

🧑‍💻 Contributing

Pull requests are welcome!
To contribute:

Fork the repository

Create a feature branch

Commit changes and push

Open a pull request

📄 License

This project is released under the MIT License.

👨‍🏫 Author

Developed by: Phineas Barasa
Email: phinbarasa36@gmail.com


