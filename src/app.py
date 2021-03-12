#===================================================================
# Imports
#===================================================================

# Flask Imports
from flask import Flask, request, render_template, redirect

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

acme = None
current_table = None

#===================================================================
# Routes
#===================================================================

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/tool')
def tool():
    global current_table
    return render_template("tool.html", table=current_table)

@app.route('/results', methods = ['POST'])
def results():
    start_date = request.form['start_date']
    print(start_date)
    return render_template("tool.html", table=current_table)

#===================================================================
# App Functionality
#===================================================================

def StartACME():
    global acme
    
    acme = ACME(True)
    acme.Login()

def BuildTable():
    pass

#===================================================================
# Run App
#===================================================================

StartACME()
if __name__ == '__main__':
    app.run(debug=True)