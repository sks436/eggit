from flask import Flask
from flask import url_for, request


app = Flask(__name__)

import config
import models
import controllers 




if __name__=='__main__':
    app.run(debug=True)