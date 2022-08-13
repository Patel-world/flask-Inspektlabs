import os
from flask import Flask,jsonify, flash, request, redirect, session,render_template, g
from werkzeug.utils import secure_filename
import sqlite3
import jwt
import functools





def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn



basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = "xcvx.com"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def login_required(function):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(function)
    def wrapped_view(**kwargs):
        print('hello')
        if g.user is None:
            print("login required")
            return redirect('/')

        return function()

    return wrapped_view    


@app.route('/login', methods=['POST'])
def login():
    data=request.get_json()
    db=get_db()
    res=jwt.decode(data['jwt'], options={"verify_signature": False})
    user = db.execute(
            "SELECT * FROM user WHERE email = ?", (res['email'],)
        ).fetchone()
    if user is None:
        
        db.execute(
                    "INSERT INTO user (email,jwt) VALUES (?, ?)",
                    (res['email'],data['jwt']),
                )
        db.commit()
        user = db.execute(
            "SELECT * FROM user WHERE email = ?", (res['email'],)
        ).fetchone()
        session.clear()
        session["user_id"] = user["id"]
        user_id = session.get("user_id")
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )
    else:
        session.clear()
        session["user_id"] = user["id"]
        user_id = session.get("user_id")
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )
    #print(jwt.decode(data['jwt'], options={"verify_signature": False}))
    #session["name"]=res['name']
    return jsonify({'status':'success'})


@app.route('/')
def index():
    db=get_db()
    posts = db.execute(
        'SELECT id, name, created, src FROM post'
        ' ORDER BY created DESC'
    ).fetchall()
    
    return render_template('index.html', posts=posts)



@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(basedir, app.config['UPLOAD_FOLDER'], filename))
            db=get_db()
            res=jwt.decode(g.user['jwt'], options={"verify_signature": False})
            db.execute(
                    "INSERT INTO post (name,src) VALUES (?, ?)",
                    (res['name'],'static/images/'+file.filename),
                )
            db.commit()

            return redirect('/')

    return render_template('upload.html')
   


@app.before_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )


@app.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    print(session)
    session.clear()
    print(session)
    return redirect('/')




