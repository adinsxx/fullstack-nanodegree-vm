# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from database_setup import Brewery, BeerName, Base, User
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
from functools import wraps

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "favoritebeerslist"

engine = create_engine('sqlite:///beerwithusers.db')
text_factory = str
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

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
    login_session['proivder] = 'google'
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

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id


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

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    #FIX THIS UNRESOLVED REFERENCE TO APP_SECRET
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id,app_secret,access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    userinfo_url = "https://graph.facebook.com/v2.2/me"
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.8/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id


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

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    url = 'https://graph.facebook.com/%s/permissions' % facebook_id
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    del login_session['facebook_id']
    return "you have been logged out"

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
@app.route('/brewery/')
def showBreweries():
    breweries = session.query(Brewery).order_by((Brewery.name))
    if 'username' not in login_session:
        return render_template('publicbreweries.html', breweries=breweries)
    else:
        return render_template('breweries.html', breweries=breweries)

@app.route('/brewery/new/', methods=['GET', 'POST'])
@login_required
def newBrewery():
    # if 'username' not in login_session:
    #     return redirect('/login')
    if request.method == 'POST':
        newBrewery = Brewery(name=request.form['name'], user_id=login_session['user_id'])
        session.add(newBrewery)
        flash('New Brewery %s Successfull Created' % newBrewery.name)
        session.commit()
        return redirect(url_for('showBreweries'))
    else:
        return render_template('newBrewery.html')

@app.route('/brewery/<int:brewery_id>/edit', methods=['GET', 'POST'])
@login_required
def editBrewery(brewery_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    editedBrewery = session.query(
        Brewery).filter_by(id=brewery_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedBrewery.name = request.form['name']
            flash('Brewery Successfully Edited %s' % editedBrewery.name)
            return redirect(url_for('showBreweries'))
    else:
        return render_template('editBrewery.html', brewery=editedBrewery)

@app.route('/brewery/<int:brewery_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteBrewery(brewery_id):
    breweryToDelete = session.query(
        Brewery).filter_by(id=brewery_id).one()
    # if 'username' not in login_session:
    #     return redirect('/login')
    if breweryToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this restaurant. Please create your own restaurant in order to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(breweryToDelete)
        flash('%s Successfully Deleted' % breweryToDelete.name)
        session.commit()
        return redirect(url_for('showBreweries', brewery_id=brewery_id))
    else:
        return render_template('deleteBrewery.html', brewery=breweryToDelete)



@app.route('/brewery/<int:brewery_id>')
@app.route('/brewery/<int:brewery_id>/menu')
def breweryMenu(brewery_id):
    brewery = session.query(Brewery).filter_by(id=brewery_id).one()
    creator = getUserInfo(brewery.user_id)
    beers = session.query(BeerName).filter_by(brewery_id=brewery.id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicbeers.html', beers=beers, brewery = brewery, creator=creator)
    else:
        return render_template('menu.html', brewery=brewery, beers=beers, creator=creator)

# Task 1: Create route for newMenuItem function here


@app.route('/brewery/<int:brewery_id>/menu/new/', methods=['GET', 'POST'])
@login_required
def newBeerName(brewery_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    brewery = session.query(Brewery).filter_by(id=brewery_id).one()
    if request.method == 'POST':
        newBeer = BeerName(name=request.form['name'], description=request.form['description'], price=request.form['price'], brewery_id=brewery_id, user_id=brewery.user_id)
        session.add(newBeer)
        session.commit()
        flash("Added a new beer dood!")
        return redirect(url_for('breweryMenu', brewery_id=brewery_id))
    else:
        return render_template('newmenuitem.html', brewery_id=brewery_id)

# Task 2: Create route for editMenuItem function here


@app.route(
    '/brewery/<int:brewery_id>/menu/<int:beer_id>/edit/',
    methods=[
        'GET',
        'POST'])
@login_required
def editBeerName(brewery_id, beer_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    editedBeer = session.query(BeerName).filter_by(id=beer_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedBeer.name = request.form['name']
        if request.form['description']:
            editedBeer.description = request.form['description']
        if request.form['price']:
            editedBeer.price = request.form['price']
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
    '/brewery/<int:brewery_id>/menu/<int:beer_id>/delete/',
    methods=[
        'GET',
        'POST'])
@login_required
def deleteBeerName(brewery_id, beer_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    brewery = session.query(Brewery).filter_by(id=brewery_id).one()
    beerToDelete = session.query(BeerName).filter_by(id=beer_id).one()
    if request.method == 'POST':
        session.delete(beerToDelete)
        session.commit()
        flash("Yeah, no one wanted that beer dood!")
        return redirect(url_for('breweryMenu', brewery_id=brewery_id))
    else:
        return render_template('deletemenuitem.html', beer=beerToDelete)

@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showBreweries'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showBreweries'))    


if __name__ == '__main__':
    app.secret_key = 'eat_my_shorts'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
