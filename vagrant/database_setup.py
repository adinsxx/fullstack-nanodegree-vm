# import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
Base = declarative_base()


class Brewery(Base):
    __tablename__ = 'brewery'
    name = Column(
        String(80), nullable=False)
    id = Column(
        Integer, primary_key=True)


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

    @property
    def serialize(self):
        return {
            'name' : self.name,
            'description' : self.description,
            'id' : self.id,
            'price' : self.price,
            'type' : self.type,
        }

#######################
engine = create_engine('sqlite:///beer.db')
Base.metadata.create_all(engine)
