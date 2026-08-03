from flask import Flask, render_template, request
from database.db import get_connection
from detect.detector import process_video
import os

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload")
def upload():
    return render_template("upload.html")


@app.route("/violations")
def violations():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM violations ORDER BY violation_time DESC"
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "violations.html",
        violations=rows
    )

@app.route("/upload_video", methods=["POST"])
def upload_video():

    file = request.files["video"]

    if file.filename == "":
        return "No file selected"

    path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(path)

    output_video = process_video(path)

    output_video = process_video(path)

    return render_template(
        "result.html",
        output_video=output_video
    )

if __name__ == "__main__":
    app.run(debug=True)