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
current_results = None

#===================================================================
# App Functionality
#===================================================================

role_groups = [
    "ALL",
    "ALL_STUDENTS",
    "ALL_HDQA",
    "STL",
    "WALK_IN",
    "ALL_PHONES",
    "ALL_CHAT_EMAIL",
    "ALL_TRAINING",
    "MEETING_AND_EVENT"
]

def StartACME():
    global acme
    
    acme = ACME(True)
    acme.Login()

def BuildTable(start_date, end_date, role_group, most_first, options):
    global current_results
    
    # Get data to work with
    data = acme.GetSchedulesInRange(start_date, end_date)
    # Filter by role
    filtered_data = acme.GetSchedulesByRole(data, role_group)
    # Get agent hours
    agent_hours = acme.GetAgentHours(filtered_data, most_first)
    # Get agent cost
    agent_cost = acme.GetScheduleCost(filtered_data)
    # Get total schedule cost
    total_cost = acme.GetScheduleCost(filtered_data, total=True)
    
    print(len(agent_hours))
    print(len(agent_cost))
    print(total_cost)
    
    current_results = total_cost

#===================================================================
# Routes
#===================================================================

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/tool')
def tool():
    global current_table
    return render_template("tool.html", results=current_results)

@app.route('/results', methods = ['GET', 'POST'])
def results():
    # Get request from form data
    form_data = request.form.to_dict(flat=False)

    start_date = form_data['start_date'][0]
    end_date = form_data['end_date'][0]
    role_group = role_groups[int(form_data['role'][0]) - 1]
    if 'most_first' in form_data:
        most_first = True
    else:
        most_first = False
    options = [0, 0]
    if 'options_1' in form_data:
        options[0] = True
        
    else:
        options[0] = False
    if 'options_2' in form_data:
        options[1] = True
        
    else:
        options[1] = False
    
    BuildTable(start_date, end_date, role_group, most_first, options)
    
    return render_template("tool.html", results=current_results)

#===================================================================
# App Utility
#===================================================================  

#===================================================================
# Run App
#===================================================================

StartACME()
if __name__ == '__main__':
    app.run(debug=True)