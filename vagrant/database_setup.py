# import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

class Brewery(Base):
    __tablename__ = 'brewery'
    name = Column(
        String(80), nullable=False)
    id = Column(
        Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'name' : self.name,
            'id' : self.id,
            'user_id' : self.user_id,
            'user' : self.user
        }


class BeerName(Base):
    __tablename__ = 'beer_name'
    name = Column(
        String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    type = Column(String(250))
    description = Column(String(250))
    price = Column(String(8))

    brewery_id = Column(
        Integer, ForeignKey('brewery.id'))
    brewery = relationship(Brewery)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'name' : self.name,
            'description' : self.description,
            'id' : self.id,
            'price' : self.price,
            'type' : self.type,
            'user_id' : self.user_id,
            'user' : self.user
        }

#######################
engine = create_engine('sqlite:///beerwithusers.db')
Base.metadata.create_all(engine)
