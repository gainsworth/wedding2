from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
from flask import Flask
import smtplib
from email.message import EmailMessage

load_dotenv()

app = Flask(__name__)


def send_email(name, party_string):

    with open('templates/thank_you_email.html', encoding='utf8') as infile:
        email_html = infile.read()
    body = email_html.format(name, party_string)
    msg = EmailMessage()
    msg.add_alternative(body, subtype='html')
    msg['Subject'] = 'See you at the wedding!'
    msg['From'] = 'info@georgeandcordelia.co.uk'
    msg['To'] = 'darknesscrazyman@hotmail.com'
    # Establish a connection to the Gmail SMTP server.
    # You might need to allow "less secure apps" in your Gmail settings.
    server = smtplib.SMTP('smtp.zoho.eu', 587)
    server.starttls()  # Upgrade the connection to encrypted SSL/TLS
    server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
    server.send_message(msg)
    server.quit()

# Use SQLite for simplicity
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rsvp.db'
db = SQLAlchemy(app)


class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=True)
    enterable = db.Column(db.String, nullable=True)
    assume_last_name = db.Column(db.String, nullable=True)
    last_name_searchable = db.Column(db.String, nullable=True)
    alternative_first_name = db.Column(db.String, nullable=True)
    family_id = db.Column(db.Integer, nullable=False)


class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    attending = db.Column(db.Boolean, nullable=False)
    updated_first_name = db.Column(db.String, nullable=False)
    updated_last_name = db.Column(db.String, nullable=True)


class AllEntries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=True)
    time_of_entry = db.Column(db.String, nullable=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/details")
def details():
    return render_template("details.html")


@app.route("/terms_and_conditions")
def terms_and_conditions():
    return render_template("terms_and_conditions.html")


@app.route('/rsvp_initial', methods=['GET', 'POST'])
def rsvp():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']

        new_entry = AllEntries(first_name=first_name, last_name=last_name,
                               email=email, time_of_entry=str(datetime.now()))
        db.session.add(new_entry)
        db.session.commit()

        guest = Guest.query.filter_by(first_name=first_name, last_name=last_name).first()

        if guest:
            family_members = Guest.query.filter_by(family_id=guest.family_id).all()
            if len(family_members) == 1:
                return redirect(url_for('thank_you'))
            return render_template('rsvp_form.html', family_members=family_members)
        else:
            return redirect(url_for('thank_you', party_string='you'))

    return render_template('rsvp_initial.html')


@app.route('/submit_rsvp', methods=['POST'])
def submit_rsvp():
    party = []
    for key in request.form:
        if key.startswith('attending_'):
            member_id = int(key.split('_')[1])
            attending = 'attending_{}'.format(member_id) in request.form
            updated_first_name = request.form['first_name_{}'.format(member_id)]
            updated_last_name = request.form.get('last_name_{}'.format(member_id))

            if attending:
                party.append(updated_first_name)

            new_rsvp = RSVP(guest_id=member_id, attending=attending,
                            updated_first_name=updated_first_name, updated_last_name=updated_last_name)
            db.session.add(new_rsvp)

    db.session.commit()

    party_string = ', '.join(['you', *party[1:-1]]) + f' and {party[-1]}'
    send_email(party[0], party_string)

    return redirect(url_for('thank_you', party_string=party_string))


@app.route('/thank_you')
def thank_you():
    party_string = request.args.get('party_string', default="")
    return render_template('thank_you.html', party_string=party_string)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure the database tables are created
    app.run(debug=True)
