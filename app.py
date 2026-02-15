from flask import Flask, render_template, request, redirect, session, send_file
import firebase_admin
from firebase_admin import credentials, db
import os
import pdfkit
from generate_resume_content import generate_resume_data
from dotenv import load_dotenv

load_dotenv()

# Flask App Setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
os.makedirs("outputs", exist_ok=True)

# PDF Generation Config
path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

# Firebase Setup
cred = credentials.Certificate("firebase_config.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://resumegenerator-dfd27-default-rtdb.firebaseio.com/'
})


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = {
            "name": request.form['name'],
            "email": request.form['email'],
            "password": request.form['password'],
            "phone": request.form['phone'],
            "location": request.form['location'],
            "linkedin": request.form['linkedin'],
            "github": request.form['github'],
            "education": [{
                "degree": request.form['degree'],
                "institution": request.form['institution'],
                "year": request.form['year'],
                "score": request.form['score']
            }],
            "internships": [{
                "company": request.form['company'],
                "field": request.form['field'],
                "title": request.form['intern_title'],
                "skills": request.form['intern_skills'],
                "desc": request.form['intern_desc']
            }],
            "achievements": request.form['achievements'].split('\n'),
            "extra_activities": request.form['activities'].split('\n'),
            "responsibilities": request.form['responsibilities'].split('\n')
        }

        db.reference(f"users/{data['email'].replace('.', '_')}").set(data)
        return redirect('/login')

    return render_template("signup.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].replace('.', '_')
        password = request.form['password']
        ref = db.reference(f"users/{email}")
        user = ref.get()

        if user and user['password'] == password:
            session['user'] = email
            return redirect('/dashboard')
        return "Invalid credentials"

    return render_template("login.html")


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    user_data = db.reference(f"users/{session['user']}").get()
    return render_template('dashboard.html', user=user_data)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user' not in session:
        return redirect('/login')

    email = session['user']
    ref = db.reference(f"users/{email}")
    user_data = ref.get()

    if request.method == 'POST':
        user_data['phone'] = request.form.get('phone', user_data['phone'])
        user_data['location'] = request.form.get('location', user_data['location'])
        user_data['linkedin'] = request.form.get('linkedin', user_data['linkedin'])
        user_data['github'] = request.form.get('github', user_data['github'])

        # ✅ Parse multiple education entries
        degrees = request.form.getlist('degree[]')
        institutions = request.form.getlist('institution[]')
        years = request.form.getlist('year[]')
        scores = request.form.getlist('score[]')
        user_data['education'] = [
            {'degree': d, 'institution': i, 'year': y, 'score': s}
            for d, i, y, s in zip(degrees, institutions, years, scores)
        ]

        # ✅ Parse multiple internship entries
        companies = request.form.getlist('company[]')
        fields = request.form.getlist('field[]')
        titles = request.form.getlist('intern_title[]')
        skills = request.form.getlist('intern_skills[]')
        descriptions = request.form.getlist('intern_desc[]')
        user_data['internships'] = [
            {'company': c, 'field': f, 'title': t, 'skills': s, 'desc': d}
            for c, f, t, s, d in zip(companies, fields, titles, skills, descriptions)
        ]

        # ✅ Parse other list fields
        user_data['achievements'] = request.form.getlist('achievements[]')
        user_data['extra_activities'] = request.form.getlist('activities[]')
        user_data['responsibilities'] = request.form.getlist('responsibilities[]')

        # ✅ Save to Firebase
        ref.set(user_data)
        return redirect('/dashboard')

    return render_template('form.html', user=user_data)


@app.route('/resume_preview', methods=['GET', 'POST'])
def resume_preview():
    if 'user' not in session:
        return redirect('/login')

    user_data = db.reference(f"users/{session['user']}").get()

    if request.method == 'POST':
        session['ai_content'] = {
            'summary': request.form.get('summary', ''),
            'skills': request.form.get('skills', '').split('\n'),
            'projects': [
                {"title": line.split(":")[0].strip(), "desc": line.split(":")[1].strip()}
                for line in request.form.get('projects', '').split('\n') if ":" in line
            ]
        }
        return redirect('/jobdesc')

    return render_template('resume_preview.html', user=user_data)


@app.route('/jobdesc', methods=['GET', 'POST'])
def jobdesc():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        job_desc = request.form.get('job_description', '').strip()
        if not job_desc:
            return "⚠️ Job description cannot be empty."

        email = session['user']
        user_data = db.reference(f"users/{email}").get()

        ai_content = generate_resume_data(user_data, job_desc)
        session['ai_content'] = ai_content

        return redirect('/resume')

    return render_template('jobdesc.html')


@app.route('/resume')
def resume():
    if 'user' not in session or 'ai_content' not in session:
        return redirect('/login')

    email = session['user']
    user_data = db.reference(f"users/{email}").get()
    ai_content = session['ai_content']

    combined_data = {
        **user_data,
        **ai_content
    }

    rendered = render_template('resume_template.html', **combined_data)

    output_html = f"outputs/{email}_resume.html"
    output_pdf = f"outputs/{email}_resume.pdf"

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(rendered)

    pdfkit.from_file(output_html, output_pdf, configuration=config, options={"page-size": "A4", "encoding": "UTF-8"})
    return send_file(output_pdf, as_attachment=True, download_name="Resume.pdf")


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
