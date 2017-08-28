# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Brewery, BeerName, Base

# Sets up the database
engine = create_engine('sqlite:///beer.db')
text_factory = str
Base.metadata.bind = engine
# Creates the session
DBSession = sessionmaker(bind=engine)
session = DBSession()

#####FIRST BREWERY & BEERS#####
brewery1 = Brewery(name="3 Floyds Brewing Co.")

session.add(brewery1)
session.commit()

beerName1 = BeerName(name="Zombie Dust", description="This intensely hopped and gushing undead Pale Ale will be one's only respite after the zombie apocalypse",
                     price="$7.00", type="American Pale Ale", brewery=brewery1)

session.add(beerName1)
session.commit()

beerName2 = BeerName(name="Robert The Bruce", description="A full-bodied Scottish-style Ale with a well-rounded malty profile and roasted biscuit-like notes",
                     price="$5.25", type="Scottish Ale", brewery=brewery1)

session.add(beerName2)
session.commit()
################################

#####SECOND BREWERY & BEERS#####
brewery2 = Brewery(name="New Glarus Brewing Company")

session.add(brewery2)
session.commit()

beerName3 = BeerName(name="Spotted Cow", description="A Wisconsin staple!!!",
                     price="$6.25", type="Cream Ale", brewery=brewery2)

session.add(beerName3)
session.commit()

beerName4 = BeerName(name="Mooon Man", description="The No-Coast Pale Ale",
                     price="$6.25", type="American Pale Ale", brewery=brewery2)

session.add(beerName4)
session.commit()

#################################

#####THIRD BREWERY & BEERS#####
brewery3 = Brewery(name="Founders Brewing Company")

session.add(brewery3)
session.commit()

beerName5 = BeerName(name="Founders Breakfast Stout", description="Brewed with flaked oats, bitter and sweetened imported chocolates, Sumatra and Kona coffee",
                     price="$6.75", type="American Double/Imperial Stout", brewery=brewery3)

session.add(beerName5)
session.commit()

beerName6 = BeerName(name="Founders Centennial IPA", description="",
                     price="$6.75", type="American IPA", brewery=brewery3)

session.add(beerName6)
session.commit()

###############################

print "added beers dude"
