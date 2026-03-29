
# from flask import Flask , render_template , request , session, redirect
# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime
# from werkzeug.utils import secure_filename
# import pymysql
# import json
# import os
# pymysql.install_as_MySQLdb()
# from dotenv import load_dotenv

# load_dotenv()

# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL")
# app.secret_key = os.getenv("SECRET_KEY")

# with open('./templates/config.json', 'r') as c:
#     params = json.load(c)["params"]

# local_server = "true"

# app = Flask(__name__)
# app.secret_key = 'super-secret-key'
# app.config['upload_folder'] = params['upload_location']

# if(local_server):
#     app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
# else:
#      app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

# db = SQLAlchemy(app)



from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import pymysql
import json
import os
from dotenv import load_dotenv

pymysql.install_as_MySQLdb()
load_dotenv()

app = Flask(__name__)

# 🔐 Secret key from .env
app.secret_key = os.getenv("SECRET_KEY")

# 📁 Config file
with open('./templates/config.json', 'r') as c:
    params = json.load(c)["params"]

# 📂 Upload folder
app.config['UPLOAD_FOLDER'] = params['upload_location']

# 🌐 Database (AUTO detect local vs production)
if os.getenv("DB_URL"):
    # 👉 Production (Render / Supabase)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL")
else:
    # 👉 Local (your PC)
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']

db = SQLAlchemy(app)





# sno, name ,email, mob,message,date
class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_number = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=False)
    email = db.Column(db.String(20), nullable=False)

class Post(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(300), nullable=False)
    img_file = db.Column(db.String(30), nullable=False)
    date = db.Column(db.String(12), nullable=False)
 


@app.route("/")
@app.route("/page/<int:page>")
def main(page=1):
    per_page = 3
    posts = Post.query.paginate(page=page, per_page=per_page)
    return render_template('index.html', params=params, posts=posts)



@app.route("/home")
def home():
    return redirect("/")
   

@app.route("/about")
def about():
    return render_template('about.html', params=params)



@app.route("/post/<string:slug>")
def post(slug):
    post = Post.query.filter_by(slug=slug).first()
    return render_template('post.html', params=params, post=post)


@app.route("/contact",methods=['GET','POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(name=name, phone_number = phone, message = message, date = datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()
    
    return render_template('contact.html', params=params)



@app.route("/dashboard",methods=['GET','POST'])
def dashbord():
    posts = Post.query.filter_by().all()
    if ('user' in session and session['user'] == params['admin_email']):
        return render_template('dashboard.html',posts=posts)
    
    if request.method == "POST":
        username = request.form.get('email')
        userproof = request.form.get('password')
        if (username == params['admin_email'] and userproof == params['admin_password']):
            session['user'] = username
            return render_template('dashboard.html',posts=posts)

    return render_template('login.html', params=params)



@app.route("/edit/<string:sno>",methods=['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_email']):
        if request.method == 'POST':
            p_title = request.form.get('post-title')
            p_slug = request.form.get('post-slug')
            p_content = request.form.get('post-content')
            p_img = request.form.get('post-img')
            date = datetime.now()

            if sno=='0':
                post = Post(sno=sno, title=p_title, slug= p_slug, content=p_content, img_file= p_img ,date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Post.query.filter_by(sno=sno).first()
                post.title = p_title
                post.slug = p_slug
                post.content = p_content
                post.img_file = p_img
                post.date = date
                db.session.commit()
                return redirect('/edit/' + str(post.sno))
            
        post = Post.query.filter_by(sno=sno).first()
        return render_template('post-edit.html', params=params, post=post)
    


@app.route("/delete/<string:sno>",methods=['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_email']):
        post = Post.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")



@app.route('/uploader',methods = ['GET','POST'])
def upload():
    if ('user' in session and session['user'] == params['admin_email']):
        if request.method == 'POST':
            f = request.files['file_upload']
            f.save(os.path.join(app.config['upload_folder'], secure_filename(f.filename)))
        return redirect("/dashboard")


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect("/dashboard")



