from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from flask_googlemaps import Map, icons
from werkzeug.exceptions import abort
import csv
from tqdm import tqdm

from src.pipeline import SearchEngine

DATA_PATH = "./data/"
NREL_PATH = DATA_PATH + "test_NREL/NREL_raw.csv"
DEFAULT_LAT = 42.30136771768067
DEFAULT_LNG = -83.71907280246434
DEFAULT_USER = -1
DEFAULT_PROMPT = None
RADIUS_DICT = {'small': 0.01, 'med': 0.03, 'large': 0.05} #TODO: change these values

bp = Blueprint('engine', __name__)
engine = SearchEngine()


@bp.route('/')
def index():
    gmap = Map(
        identifier="gmap",
        varname="gmap",
        lat=DEFAULT_LAT,
        lng=DEFAULT_LNG,
        style="height:40vmax;width:80vmax;margin:50px;",
    )
    return render_template("engine/index.html", gmap=gmap)


@bp.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        lat = request.form['lat']
        lng = request.form['lng']
        prompt = request.form['prompt'] if 'prompt' in request.form else DEFAULT_PROMPT
        try:
            user_id = int(request.form['user_id'])
        except:
            user_id = DEFAULT_USER
        sort_by = request.form['sort']
        radius = request.form['radius']
        session['sort_by'] = sort_by
        session['radius'] = radius
        session['user_id'] = user_id
        session['lat'] = lat
        session['lng'] = lng
        session['prompt'] = prompt
        error = None

        if not lat or not lng:
            error = 'Latitude and Longitude are required.'

        if sort_by == 'distance':
            engine.set_reranker()
        elif sort_by == 'base':
            engine.set_reranker('vector')
        elif sort_by == 'cf':
            if user_id == DEFAULT_USER or user_id == None:
                error = 'User ID is required for collaborative filtering.'
            engine.set_reranker('vector+cf')
        else:
            error = 'Invalid sort_by parameter.'

        if radius in RADIUS_DICT:
            radius = RADIUS_DICT[radius]
        else:
            error = 'Invalid radius parameter.'

        res_details = [] #ADDED this line to avoid return error
        if error is not None:
            flash(error)
        else:
            result = engine.get_results_all(
                lat, lng, prompt, int(user_id), radius)
            if result:
                print("Result: ")
                #print(result)
                res_details = engine.get_station_info(result)
                marker_t = {
                    "icon": icons.dots.blue,
                    "lat": None,
                    "lng": None,
                    "infobox": None
                }
                markers = []
                for i in range(len(res_details)):
                    marker_t["lat"] = res_details[i]['latitude']
                    marker_t["lng"] = res_details[i]['longitude']
                    marker_t["infobox"] = f"{res_details[i]['station_name']}<br>{res_details[i]['street_address']}<br>{res_details[i]['ev_network']}"
                    markers.append(marker_t.copy())
                gmap = Map(
                    identifier="gmap",
                    varname="gmap",
                    lat=float(lat),
                    lng=float(lng),
                    markers=markers,
                    style="height:40vmax;width:80vmax;margin:50px;",
                )
            else:
                print("No Result")
                res_details = []
                gmap = Map(
                    identifier="gmap",
                    varname="gmap",
                    lat=float(lat),
                    lng=float(lng),
                    style="height:40vmax;width:80vmax;margin:50px;",
                )

    else:
        sort_by = session.get('sort_by', 'distance')
        radius = session.get('radius', 'small')
        user_id = session.get('user_id', DEFAULT_USER)
        lat = session.get('lat', DEFAULT_LAT)
        lng = session.get('lng', DEFAULT_LNG)
        prompt = session.get('prompt', '')
        res_details = []
        gmap = Map(
            identifier="gmap",
            varname="gmap",
            lat=lat,
            lng=lng,
            style="height:40vmax;width:80vmax;margin:50px;",
        )

    #TODO: print(res_details) ##ADDED
    return render_template(
        'engine/index.html',
        lat=lat,
        lng=lng,
        prompt=prompt,
        user_id=user_id,
        results=res_details,
        gmap=gmap,
        sort_by=sort_by,
        radius=radius
    )
