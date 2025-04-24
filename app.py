from flask import Flask, render_template, request, redirect, flash, session,url_for
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os
load_dotenv()
app=Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
mysql=MySQL(app)

@app.route('/',methods=['GET'])
def index():
    return render_template("Auth.html")

@app.route('/signup',methods=['POST'])
def signup():
    username = request.form['username']
    phone = request.form['phone']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    role=request.form['role']

    if password != confirm_password:
        flash("Password do not match")
        return redirect('/') 
    
    cur=mysql.connection.cursor()
    cur.execute("INSERT INTO users (username, phone, email, password,role) VALUES (%s, %s, %s, %s,%s)",(username, phone, email, password,role))
    mysql.connection.commit()
    cur.close()

    flash("Account Created Sucessfully.")
    return redirect('/')
@app.route('/login',methods=['POST'])
def login():
    username=request.form['username']
    password=request.form['password']

    cur=mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s and password=%s",(username,password))
    user=cur.fetchone()
    cur.execute("SELECT role FROM users WHERE username=%s and password=%s",(username,password))
    role=cur.fetchone()
    cur.close()

    if user:
        session["username"]=user[1]
        session["role"]=user[5]
        session["email"]=user[3]
        flash("Login successful!")
        if user[5]=="Job Seeker":
            return redirect("/jobseek")
        elif user[5]=="Employer":
            return redirect("/employer")
        else:
            return redirect('/admin')
    
    else:
        flash("Invalid username or password!")
        return redirect('/')

@app.route('/jobseek')
def jobseek():
    cur=mysql.connection.cursor()
    cur.execute("SELECT * FROM jobs")
    jobs=cur.fetchall()
    username = session['username']
    email=session['email']
    cur.execute("SELECT * FROM applications WHERE name = %s", (username,))
    applications = cur.fetchall()
    cur.execute("SELECT job_id FROM applications WHERE email = %s", (email,))
    applied_jobs = [row[0] for row in cur.fetchall()]
    cur.close()
    if 'username' in session:
        return render_template('Jobseek.html', username=username,jobs=jobs,email=email,applications=applications,applied_jobs=applied_jobs)
    else:
        flash("Please log in first!")
        return redirect('/')

@app.route('/apply/<int:job_id>', methods=['POST'])
def apply(job_id):
    name=request.form['name']
    email=request.form['email']
    cur=mysql.connection.cursor()
    cur.execute("SELECT * FROM applications WHERE job_id = %s AND email = %s", (job_id, email))
    existing = cur.fetchone()
    if existing:
        flash("You have already applied to this job.")
        return redirect(request.referrer)
    id=job_id
    cur.execute("INSERT INTO applications (job_id, name, email) VALUES (%s, %s, %s)", (id, name, email))
    mysql.connection.commit()
    cur.close()
    flash("Applied Sucessfully")
    return redirect('/jobseek')


@app.route('/employer')
def employer():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM jobs")
    jobs = cur.fetchall()
    cur.execute("SELECT * FROM applications")
    applications=cur.fetchall()
    cur.close()
    if 'username' in session:
        return render_template('Employer.html', username=session['username'],jobs=jobs,applications=applications)
    else:
        flash("Please log in first!")
        return redirect('/')

@app.route('/admin')
def admin():
    cur=mysql.connection.cursor()
    cur.execute('SELECT * FROM users;')
    users=cur.fetchall()
    cur.execute('SELECT * FROM jobs;')
    jobs=cur.fetchall()
    return render_template('Admin.html',users=users,jobs=jobs)

@app.route('/post',methods=['POST'])
def post():
    title=request.form['title']
    company=request.form['company']
    location=request.form['location']
    type = request.form['type']
    description = request.form['description']

    cur=mysql.connection.cursor()
    cur.execute("INSERT INTO jobs (title, company, location, type, description) VALUES (%s, %s, %s, %s, %s)",(title, company, location, type, description))
    mysql.connection.commit()
    cur.close()
    return redirect("/employer")

@app.route('/edit/<int:job_id>',methods=['GET'])
def edit(job_id):
    cur=mysql.connection.cursor()
    cur.execute("SELECT * FROM jobs WHERE id = %s",(job_id,))
    job=cur.fetchone()
    cur.close()
    return render_template("editjob.html",job=job)

@app.route('/update/<int:job_id>',methods=['POST'])
def update(job_id):
    title=request.form['title']
    company=request.form['company']
    location=request.form['location']
    type = request.form['type']
    description = request.form['description']

    cur=mysql.connection.cursor()
    cur.execute("UPDATE jobs SET title=%s, company=%s, location=%s, type=%s, description=%s WHERE id=%s",(title, company, location, type, description, job_id))
    mysql.connection.commit()
    cur.close()
    return redirect('/employer')

@app.route('/delete/<int:job_id>',methods=['GET'])
def delete(job_id):
    cur=mysql.connection.cursor()
    cur.execute("DELETE FROM jobs WHERE id = %s",(job_id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/employer')

@app.route('/update_status/<int:app_id>/<status>')
def update_status(app_id, status):
    if status not in ['Accepted', 'Rejected']:
        flash("Invalid status.")
        return redirect('/employer')
    cur = mysql.connection.cursor()
    cur.execute("UPDATE applications SET status = %s WHERE id = %s", (status, app_id))
    mysql.connection.commit()
    cur.close()
    return redirect('/employer')

@app.route('/edit_user/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    username = request.form['username']
    phone = request.form['phone']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET username = %s, phone = %s, email = %s, password = %s, role = %s WHERE id = %s", (username, phone, email, password, role, user_id))
    mysql.connection.commit()
    cur.close()
    flash("User role updated successfully.")
    return redirect('/admin')

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    cur=mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE id=%s",(user_id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/admin')

@app.route('/delete_job/<int:job_id>')
def delete_job(job_id):
    cur=mysql.connection.cursor()
    cur.execute("DELETE FROM jobs WHERE id=%s",(job_id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/admin')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully.")
    return redirect('/')

if __name__=="__main__":
    app.run(debug=False,host='0.0.0.0')
