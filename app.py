from flask import Flask, render_template, request, redirect, url_for
from googlesearch import search
from flask_sqlalchemy import SQLAlchemy
import math
from datetime import datetime 

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rankings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()

# Define the database model
class User(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(2048), nullable=False)
    keywords = db.Column(db.String(200), nullable=False)
    rank = db.Column(db.Integer)
    page = db.Column(db.Integer)
    region = db.Column(db.String(10))
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User %r>' % self.username
    
def init_db():
    db.create_all()

# Home page route
@app.route('/')
def index():
    rows = User.query.order_by(User.date_submitted.desc()).all()
    no_data = len(rows) == 0
    return render_template('index.html', rows=rows, no_data=no_data)

# Check rank route
@app.route('/', methods=['POST'])
def check_rank():
    domain = request.form['domain']
    keywords = request.form['keywords'].split(',')  # Split keywords by comma
    region = request.form['region']

    # Determine top-level domain based on region
    if region == "1":
        domain_tld = "com"
        region_name = "USA"
        print('The search is in USA - Google')
    elif region == "2":
        domain_tld = "com.pk"
        region_name = "Pakistan"
        print('The search is in Pakistan - Google')

    results = []

    # Function to search for keyword ranks
    def searchfunc(my_website):
        print(
            f'Welcome to SEO Python keyword Rank finder!\n Your domain is: {my_website}'
        )
        print("Your keywords are: ", keywords)
        print('\n\nSearching the whole Google for you...\n\n')

        y = 0
        for keyword in keywords:
            urls = search(keyword, tld=domain_tld, num=100, stop=100, pause=2)

            found = False
            for index, url in enumerate(urls):
                if my_website in url:
                    page = math.ceil((index+1)/10)
                    rank = index+1
                    results.append({"keyword": keyword, "rank": rank, "page": page, "url":url})
                    found = True
                    break

            if not found:
                results.append({"keyword": keyword, "rank": "Not Found", "page": "Not Found"})
            y += 1

    # Call the search function
    searchfunc(domain)

    for result in results:
        user = User(domain=domain, keywords=result["keyword"], rank=result["rank"], page=result["page"], region=region_name)
        db.session.add(user)
    db.session.commit()
  
    return redirect(url_for('index'))

# Route to handle entry deletion
@app.route('/delete/<int:sno>', methods=['POST'])
def delete_entry(sno):
    entry = User.query.get_or_404(sno)
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port='9000')
