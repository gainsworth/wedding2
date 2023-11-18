from flask import Flask, render_template, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from sqlalchemy import or_
from datetime import datetime
import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
import csv
import io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


def generate_csv_attachment(model, headers, filename):
    """Generate an in-memory CSV attachment from a given SQLAlchemy model"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write the header
    writer.writerow(headers)

    # Query and write the rows
    rows = model.query.all()
    for row in rows:
        writer.writerow([getattr(row, header) for header in headers])

    # Convert the in-memory text file to bytes for attachment
    output.seek(0)
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(output.getvalue().encode('utf-8'))
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')

    return part


def send_george_email(name, party_string, attach_csvs=True):
    # Create a multipart message
    msg = MIMEMultipart()
    msg['Subject'] = 'See you at the wedding!'
    msg['From'] = 'info@georgeandcordelia.co.uk'
    msg['To'] = 'george.ainsworth@hotmail.co.uk'

    # Add your HTML message
    with open('templates/thank_you_email.html', encoding='utf8') as infile:
        email_html = infile.read()
    body = email_html.format(name, party_string)
    msg.attach(MIMEText(body, 'html'))

    # If we need to attach CSVs
    if attach_csvs:
        # Attach AllEntries CSV
        all_entries_headers = ["id", "first_name", "last_name", "email", "time_of_entry"]
        # noinspection PyTypeChecker
        all_entries_part = generate_csv_attachment(AllEntries, all_entries_headers, "all_entries.csv")
        msg.attach(all_entries_part)

        # Attach RSVP CSV
        rsvp_headers = ["id", "guest_id", "attending", "updated_first_name", "updated_last_name"]
        # noinspection PyTypeChecker
        rsvp_part = generate_csv_attachment(RSVP, rsvp_headers, "rsvp.csv")
        msg.attach(rsvp_part)

    # Now, the sending part remains unchanged:
    server = smtplib.SMTP('smtp.zoho.eu', 587)
    server.starttls()
    server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
    server.send_message(msg)
    server.quit()


load_dotenv()

app = Flask(__name__)
Talisman(app)


def send_email(name, party_string, email):
    with open('templates/thank_you_email.html', encoding='utf8') as infile:
        email_html = infile.read()
    body = email_html.format(name, party_string)
    msg = EmailMessage()
    msg.add_alternative(body, subtype='html')
    msg['Subject'] = 'See you at the wedding!'
    msg['From'] = 'info@georgeandcordelia.co.uk'
    msg['To'] = email
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

migrate = Migrate(app, db)


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
    email = db.Column(db.String, nullable=False)


class AllEntries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=True)
    time_of_entry = db.Column(db.String, nullable=True)


@app.route("/home")
def index():
    return render_template("index.html")


@app.route("/details")
def details():
    return render_template("details.html")


@app.route("/terms_and_conditions")
def terms_and_conditions():
    return render_template("terms_and_conditions.html")


@app.route('/', methods=['GET', 'POST'])
def rsvp():
    if request.method == 'POST':
        first_name = request.form['first_name'].title().strip()
        last_name = request.form['last_name'].title().strip()
        email = request.form['email'].strip()

        new_entry = AllEntries(first_name=first_name, last_name=last_name,
                               email=email, time_of_entry=str(datetime.now()))
        db.session.add(new_entry)
        db.session.commit()

        guest_search = Guest.query.filter(
            or_(Guest.first_name == first_name, Guest.alternative_first_name == first_name),
            Guest.last_name == last_name,
            Guest.enterable != 'No').first()

        if not guest_search:
            guest_search = Guest.query.filter(
                or_(Guest.first_name == first_name, Guest.alternative_first_name == first_name),
                Guest.last_name == '',
                Guest.enterable != 'No').first()

        if not guest_search:
            guest_search = Guest.query.filter(Guest.last_name_searchable == 'Yes',
                                              Guest.last_name == last_name,
                                              Guest.enterable != 'No').first()
        guest = guest_search
        if guest:
            main_id = guest.id
            family_members = Guest.query.filter_by(family_id=guest.family_id).all()
            if len(family_members) == 1:
                if [x.email for x in AllEntries.query.all()].count(email) == 1 \
                        or email == 'darknesscrazyman@hotmail.com':
                    send_email(first_name, 'you', email)
                    send_george_email(first_name, 'you', attach_csvs=True)
                new_rsvp = RSVP(guest_id=guest.id, attending=True,
                                updated_first_name=first_name, updated_last_name=last_name, email=email)
                db.session.add(new_rsvp)
                db.session.commit()
                return render_template('thank_you.html', party_string='you', first_name=first_name)
            else:
                # main_guest = Guest(number=guest.number, first_name=first_name, last_name=last_name, enterable='Yes',
                #                    assume_last_name='', last_name_searchable='', alternative_first_name='',
                #                    family_id=guest.family_id)
                guest.first_name = first_name
                guest.last_name = last_name
                return render_template('rsvp_form.html', family_members=family_members, email=email, main_id=main_id)
        else:
            if [x.email for x in AllEntries.query.all()].count(email) == 1 or email == 'darknesscrazyman@hotmail.com':
                send_email(first_name, 'you', email)
                send_george_email(first_name, 'you', attach_csvs=True)
            # new_rsvp = RSVP(guest_id=-1, attending=True,
            #                 updated_first_name=first_name, updated_last_name=last_name)
            # db.session.add(new_rsvp)
            return render_template('thank_you.html', party_string='you', first_name=first_name)
            # return redirect(url_for('thank_you', party_string='you'))

    return render_template('rsvp_initial.html')


@app.route('/submit_rsvp', methods=['POST'])
def submit_rsvp():
    party = []
    main_id = request.form['main_id']
    email = request.form['email']
    for key in request.form:
        if key.startswith('attending_'):
            member_id = int(key.split('_')[1])
            attending = 'attending_{}'.format(member_id) in request.form
            updated_first_name = request.form['first_name_{}'.format(member_id)]
            updated_last_name = request.form.get('last_name_{}'.format(member_id))

            if attending:
                print(member_id, main_id, updated_first_name, member_id == main_id, type(member_id), type(main_id))
                party.append(updated_first_name if member_id != int(main_id) else 'you')
                if member_id == main_id:
                    name = updated_first_name
                print(party)

            new_rsvp = RSVP(guest_id=member_id, attending=attending,
                            updated_first_name=updated_first_name, updated_last_name=updated_last_name, email=email)
            db.session.add(new_rsvp)

    db.session.commit()

    party.sort(key=lambda k: 0 if k == 'you' else 1)
    party_string = ', '.join(party[:-1]) + f'{" and " + party[-1] if len(party) > 1 else ""}'
    if [x.email for x in AllEntries.query.all()].count(email) == 1 or email == 'darknesscrazyman@hotmail.com':
        send_email(party[0], party_string, email)
        send_george_email(party[0], party_string, attach_csvs=True)

    return render_template('thank_you.html', party_string=party_string, first_name=name)
    # return redirect(url_for('thank_you', party_string=party_string))


# @app.route('/thank_you')
# def thank_you():
#     party_string = request.args.get('party_string', default="")
#     return render_template('thank_you.html', party_string=party_string)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure the database tables are created
    app.run(debug=True)
