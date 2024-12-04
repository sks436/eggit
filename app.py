import controllers_admin
import controllers_login
import controllers
import models
import config
from flask import Flask
from flask import url_for, request


app = Flask(__name__)


if __name__ == "__main__":
    app.run(debug=True)
