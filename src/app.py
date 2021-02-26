#===================================================================
# Imports
#===================================================================

# Flask Imports
from flask import Flask, request, render_template

# Backend Imports
from ACME import ACME

# Utility Imports
import os
import io

#===================================================================
# App Configuration
#===================================================================

app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')

#===================================================================
# Routes
#===================================================================

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/tool')
def tool():
    return render_template("tool.html")

#===================================================================
# Run App
#===================================================================

if __name__ == '__main__':
    app.run(debug=True)