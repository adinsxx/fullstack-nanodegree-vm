from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

from database_setup import Brewery, BeerName, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "favoritebeerslist"

engine = create_engine('sqlite:///beer.db')
text_factory = str
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/brewery/<int:brewery_id>/menu/JSON')
def breweryMenuJSON(brewery_id):
    brewery = session.query(Brewery).filter_by(id=brewery_id).one()
    beers = session.query(BeerName).filter_by(brewery_id=brewery.id)
    return jsonify(BeerNames=[i.serialize for i in beers])


@app.route('/brewery/<int:brewery_id>/menu/<int:beer_id>/JSON')
def beerNameJSON(brewery_id, beer_id):
    beerName = session.query(BeerName).filter_by(id=beer_id).one()
    return jsonify(beerName=beerName.serialize)


@app.route('/brewery/JSON')
def breweryJSON():
    brewery = session.query(Brewery).all()
    return jsonify(brewery=[r.serialize for r in brewery])


@app.route('/')
@app.route('/brewery/<int:brewery_id>/')
def breweryMenu(brewery_id):
    brewery = session.query(Brewery).filter_by(id=brewery_id).one()
    beers = session.query(BeerName).filter_by(brewery_id=brewery.id)
    return render_template('menu.html', brewery=brewery, beers=beers)

# Task 1: Create route for newMenuItem function here


@app.route('/brewery/<int:brewery_id>/new/', methods=['GET', 'POST'])
def newBeerName(brewery_id):
    if request.method == 'POST':
        newBeer = BeerName(name=request.form['name'], brewery_id=brewery_id)
        session.add(newBeer)
        session.commit()
        flash("Added a new beer dood!")
        return redirect(url_for('breweryMenu', brewery_id=brewery_id))
    else:
        return render_template('newmenuitem.html', brewery_id=brewery_id)

# Task 2: Create route for editMenuItem function here


@app.route(
    '/brewery/<int:brewery_id>/<int:beer_id>/edit/',
    methods=[
        'GET',
        'POST'])
def editBeerName(brewery_id, beer_id):
    editedBeer = session.query(BeerName).filter_by(id=beer_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedBeer.name = request.form['name']
        session.add(editedBeer)
        session.commit()
        flash("Yeah, fixed that beer dood!")
        return redirect(url_for('breweryMenu', brewery_id=brewery_id))
    else:
        # USE THE RENDER_TEMPLATE FUNCTION BELOW TO SEE THE VARIABLES YOU
        # SHOULD USE IN YOUR EDITMENUITEM TEMPLATE
        return render_template(
            'editmenuitem.html',
            brewery_id=brewery_id,
            beer_id=beer_id,
            beer=editedBeer)

# Task 3: Create a route for deleteMenuItem function here


@app.route(
    '/brewery/<int:brewery_id>/<int:beer_id>/delete/',
    methods=[
        'GET',
        'POST'])
def deleteBeerName(brewery_id, beer_id):
    beerToDelete = session.query(BeerName).filter_by(id=beer_id).one()
    if request.method == 'POST':
        session.delete(beerToDelete)
        session.commit()
        flash("Yeah, no one wanted that beer dood!")
        return redirect(url_for('breweryMenu', brewery_id=brewery_id))
    else:
        return render_template('deletemenuitem.html', beer=beerToDelete)


if __name__ == '__main__':
    app.secret_key = 'eat_my_shorts'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
