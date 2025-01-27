from flask import Flask, request, Response
import pickle
import src.get_address_neigh as gan
from flask import render_template
from flask import Markup
import os
import locale
locale.setlocale(locale.LC_MONETARY, '')

app=Flask(__name__)

SQ_METERS=80
ROOMS=2
BATHROOMS=2
FLOOR=3
RENEWAL_NEEDED="No"
NEW_DEVELOPMENT="No"
EXTERIOR="Yes"
PARKING="Yes"
LIFT = "Yes"
LATI=40.41
LONGI=-3,70
ADDRESS = "ironhack madrid"
Y = ""

# necesario en pythonanywhere
PATH=os.path.dirname(os.path.abspath(__file__))

#load Machine Learning model before first request to the server
@app.before_first_request
def startup():
    global model
    global read_barrios 
    global read_punt
    global pisos
    filename = '/data/outputs/Extra_Trees_ML_Model/ExtraTrees_model.sav'
    model = pickle.load(open(PATH+f'{filename}', 'rb'))
    read_barrios= gan.read_barrios()
    read_punt = gan.read_barr_punt()
    pisos = gan.read_inmuebles_staditicas()

@app.route('/') 
def welcome():
     return {                                                                                                                                
        "1.status": "OK",
        "2.message": "Welcome to idealisto-api",
        "3.Available endpoints": "" ,
        "A.--> /find/": "Introduce the property data and get the appraisal price",
        "B.--> /web/": "Soon Available. Working on more functions!!"
    }
# main app
@app.route("/find", methods=['POST', 'GET'])
def main():
    
    if request.method=='POST':
        
        s_sq_meters =request.form['s_sq_meters']
        s_rooms=request.form['s_rooms']
        s_bathrooms=request.form['s_bathrooms']
        s_floor=request.form['s_floor']
        s_renewal_needed=request.form['s_renewal_needed']
        s_new_development=request.form['s_new_development']
        s_lift=request.form['s_lift']
        s_exterior=request.form['s_exterior']
        s_parking=request.form['s_parking']
        s_address=request.form['s_address']
        
        # reassigns for prediction
        meters =int(s_sq_meters)
        rooms =int(s_rooms)
        bathrooms =int(s_bathrooms)
        floor =int(s_floor)
        renewal=1 if s_renewal_needed=="Yes" else 0
        new=1 if s_new_development=="Yes" else 0
        lift=1 if s_lift=="Yes" else 0
        exterior=1 if s_exterior=="Yes" else 0
        parking=1 if s_parking=="Yes" else 0
        
        #gets neighbourhood data for the prediction 
        get_coord = gan.get_coordinates(s_address)
        coord = gan.coordintes2gdf(get_coord)
        barrio = gan.get_barrio(coord,read_barrios)
        security,transport,health,education = gan.get_punt(barrio,read_punt)
        area_price = gan.get_nearest_point(pisos,coord)
        lat = get_coord["lat"]
        lng = get_coord["lng"]
        print(security,transport,health,education,lat,lng)
        
        # property data for the prediction model
        piso=[[meters,rooms,bathrooms,floor,area_price,renewal,
        new,lift,exterior,parking,lat,lng,security,transport,health,
        education]]
        print(piso)
        
        # prediction
        y_prob= locale.currency(model.predict(piso),grouping=True)
        
               
        return render_template('index.html',
            s_sq_meters =s_sq_meters,
            s_rooms=s_rooms,
            s_bathroooms=s_bathrooms,
            s_floor=s_floor,
            s_renewal_needed=s_renewal_needed,
            s_new_development=s_new_development,
            s_lift=s_lift,
            s_exterior=s_exterior,
            s_parking=s_parking,
            s_address=s_address,
            y_prob=y_prob)
            
          
    else:
        # parameters by default
        return render_template('index.html',
            s_sq_meters=SQ_METERS,
            s_rooms =ROOMS,
            s_bathrooms =BATHROOMS,
            s_floor =FLOOR,
            s_renewal_needed =RENEWAL_NEEDED,
            s_new_development =NEW_DEVELOPMENT,
            s_lift=LIFT,
            s_exterior =EXTERIOR,
            s_parking =PARKING,
            s_address=ADDRESS,
            y_prob = Y)


if __name__== '__main__':
    app.run(debug=True)