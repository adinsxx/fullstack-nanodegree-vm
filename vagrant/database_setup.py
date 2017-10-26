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
    beer_name = relationship('BeerName', cascade='all, delete-orphan')

    @property
    def serialize(self):
        return {
            'name' : self.name,
            'id' : self.id,
            'user_id' : self.user_id
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
            'user_id' : self.user_id
        }

#######################
engine = create_engine('postgres://svymsdhuczbetf:89fa6e925141ea7471c235b6695ee5bfe823a3339658c10f79b22ebeadd9b570@ec2-54-243-58-69.compute-1.amazonaws.com:5432/dbltor7fnb7jee')
Base.metadata.create_all(engine)
