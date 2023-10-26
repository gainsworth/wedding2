from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Use SQLite for simplicity
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://eptvybculedrhx:6e1e6290f596b73b6888d884c2b33e0fecb3759571726b9be982a313f8c40eb5@ec2-34-242-154-118.eu-west-1.compute.amazonaws.com:5432/dr0rgp061as0v'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rsvp.db'
db = SQLAlchemy(app)


# class Guest(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     number = db.Column(db.Integer, nullable=False)
#     first_name = db.Column(db.String, nullable=False)
#     last_name = db.Column(db.String, nullable=True)
#     enterable = db.Column(db.String, nullable=True)
#     assume_last_name = db.Column(db.String, nullable=True)
#     last_name_searchable = db.Column(db.String, nullable=True)
#     alternative_first_name = db.Column(db.String, nullable=True)
#     family_id = db.Column(db.Integer, nullable=False)
#
#
# class RSVP(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
#     attending = db.Column(db.Boolean, nullable=False)
#     updated_first_name = db.Column(db.String, nullable=False)
#     updated_last_name = db.Column(db.String, nullable=True)
#
#
# class AllEntries(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     first_name = db.Column(db.String, nullable=False)
#     last_name = db.Column(db.String, nullable=True)
#     email = db.Column(db.String, nullable=True)
#     time_of_entry = db.Column(db.String, nullable=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/details")
def details():
    return render_template("details.html")


@app.route('/rsvp_initial', methods=['GET', 'POST'])
def rsvp():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']

        # new_entry = AllEntries(first_name=first_name, last_name=last_name,
        #                        email=email, time_of_entry=str(datetime.now()))
        # db.session.add(new_entry)
        # db.session.commit()
        #
        # guest = Guest.query.filter_by(first_name=first_name, last_name=last_name).first()
        #
        # if guest:
        #     family_members = Guest.query.filter_by(family_id=guest.family_id).all()
        #     return render_template('rsvp_form.html', family_members=family_members)
        # else:
        #     return "Guest not found", 404

    return render_template('rsvp_initial.html')


@app.route('/submit_rsvp', methods=['POST'])
def submit_rsvp():
    for key in request.form:
        if key.startswith('attending_'):
            member_id = int(key.split('_')[1])
            attending = 'attending_{}'.format(member_id) in request.form
            updated_first_name = request.form['first_name_{}'.format(member_id)]
            updated_last_name = request.form.get('last_name_{}'.format(member_id))

            # new_rsvp = RSVP(guest_id=member_id, attending=attending,
            #                 updated_first_name=updated_first_name, updated_last_name=updated_last_name)
            # db.session.add(new_rsvp)

    db.session.commit()

    return redirect(url_for('thank_you'))


@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')


# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()  # Ensure the database tables are created
#     app.run(debug=True)
