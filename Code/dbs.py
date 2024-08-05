import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

cur_dir=os.path.abspath(os.path.dirname(__file__))
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///"+os.path.join(cur_dir,"databases/lms.db")
db=SQLAlchemy()
db.init_app(app)
app.app_context().push()

class User(db.Model):
    __tablename__="user"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    requests = db.relationship('Request', backref='user')
    feedbacks=db.relationship('Feedback',backref='user')

class Admin(db.Model):
    __tablename__="admin"
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    
class Section(db.Model):
    __tablename__="section"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String, unique=True)
    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    description = db.Column(db.String)
    books = db.relationship('Book', backref='section')

class Book(db.Model):
    __tablename__="book"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    author_id=db.Column(db.Integer, db.ForeignKey('author.id'))
    total_copies = db.Column(db.Integer, nullable=False)
    date_added = db.Column(db.DateTime, default = datetime.utcnow)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    requests = db.relationship('Request', backref='book')
    feedbacks=db.relationship('Feedback',backref='book')

class Author(db.Model):
    __tablename__="author"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.Integer, nullable=False)
    books = db.relationship('Book', backref='author')

class Request(db.Model):
    __tablename__="request"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    issue_date = db.Column(db.DateTime)
    status = db.Column(db.String, nullable=False)
    
class Feedback(db.Model):
    __tablename__="feedback"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    text = db.Column(db.String, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime)