from flask import Flask, render_template, request, flash

app = Flask(__name__)
app.secret_key = "gandc-wedding-key"


@app.route("/")
def base():
    return render_template("home.html")


@app.route("/rsvp", methods=["POST", "GET"])
def rsvp():
    flash("Please RSVP below")
    return render_template("rsvp.html")
#
# @app.route("/other-shit", methods=["POST", "GET"])
# def greeter():
#     flash("Hi " + str(request.form['name_input']) + ", great to see you!")
#     return render_template("base.html")
