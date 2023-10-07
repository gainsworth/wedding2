from flask import Flask, render_template, request, flash

app = Flask(__name__)
app.secret_key = "gandc-wedding-key"


@app.route("/rsvp")
def index():
    flash("Please RSVP below")
    return render_template("index.html")


@app.route("/other-shit", methods=["POST", "GET"])
def greeter():
    flash("Hi " + str(request.form['name_input']) + ", great to see you!")
    return render_template("index.html")
