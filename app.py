from flask import Flask, render_template, request, session, redirect,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()

app = Flask(__name__)

# 🔐 Secret key
app.secret_key = os.getenv("SECRET_KEY")

# ⚙️ Params (non-sensitive + useful stuff)
params = {
    "blog_name": os.getenv("BLOG_NAME"),
    "tag_line": os.getenv("TAG_LINE"),
    "admin_email": os.getenv("ADMIN_EMAIL"),
    "admin_password": os.getenv("ADMIN_PASSWORD"),
    "upload_location": os.getenv("UPLOAD_LOCATION")
}

# 📂 Upload folder
app.config['UPLOAD_FOLDER'] = params["upload_location"]

# 🌐 Supabase PostgreSQL (ONLY THIS)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL")

# ⚠️ Required for Supabase (SSL)
if "supabase" in str(os.getenv("DB_URL")):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "connect_args": {"sslmode": "require"},
        "pool_pre_ping": True
    }

# ✅ Recommended
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 🗄️ Init DB
db = SQLAlchemy(app)

@app.context_processor
def inject_globals():
    return dict(
        blog_name=os.getenv("BLOG_NAME"),
        blog_tagline=os.getenv("BLOG_TAGLINE")
    )

# sno, name ,email, mob,message,date
class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)  
    message = db.Column(db.Text, nullable=False)  
    date = db.Column(db.DateTime, default=datetime.utcnow)
    email = db.Column(db.String(100), nullable=False)

class Post(db.Model):
    __tablename__ = "post"

    sno = db.Column(db.Integer, primary_key=True, autoincrement=True)

    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(150), nullable=False, unique=True)

    content = db.Column(db.Text, nullable=False)   # ✅ unlimited text

    img_file = db.Column(db.String(200), nullable=True)

    date = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ auto date

    def __repr__(self):
        return f"<Post {self.title}>"

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


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():

    # ✅ Already logged in
    if 'user' in session and session['user'] == params['admin_email']:
        posts = Post.query.all()
        return render_template('dashboard.html', posts=posts)

    # ✅ Login attempt
    if request.method == "POST":
        username = request.form.get('email')
        password = request.form.get('password')

        print("Entered:", username, password)
        print("Actual:", params['admin_email'], params['admin_password'])

        if username == params['admin_email'] and password == params['admin_password']:
            session['user'] = username
            flash("Login successful!", "success")
            return redirect("/dashboard")
        else:
            flash("Invalid credentials!", "danger")

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
                post = Post(title=p_title, slug= p_slug, content=p_content, img_file= p_img ,date=date)
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
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        return redirect("/dashboard")


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect("/dashboard")



