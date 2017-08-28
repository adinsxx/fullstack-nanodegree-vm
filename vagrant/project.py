from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

from database_setup import Brewery, BeerName, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///beer.db')
text_factory = str
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


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
        return redirect(url_for('breweryMenu', brewery_id=brewery_id))
    else:
        return render_template('newmenuitem.html', brewery_id=brewery_id)

# Task 2: Create route for editMenuItem function here


@app.route('/brewery/<int:brewery_id>/<int:beer_id>/edit/')
def editBeerName(brewery_id, beer_id):
    return "page to edit a menu item. Task 2 complete!"

# Task 3: Create a route for deleteMenuItem function here


@app.route('/brewery/<int:brewery_id>/<int:beer_id>/delete/')
def deleteBeerName(brewery_id, beer_id):
    return "page to delete a menu item. Task 3 complete!"


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
