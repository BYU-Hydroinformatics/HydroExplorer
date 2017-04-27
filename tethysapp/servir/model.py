from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String
from sqlalchemy.orm import sessionmaker

from .app import ServirCatalog #App base class from app.py

#Connecting to the persistent store engine
engine = ServirCatalog.get_persistent_store_engine('catalog_db')
SessionMaker = sessionmaker(bind=engine)
Base = declarative_base()

#Declaring the persistent store base class
class Catalog(Base):

    #Creating a table called hydroservers
    __tablename__ = 'hydroservers'

    # Table Columns

    id = Column(Integer, primary_key = True) #Record number.
    title = Column(String(50)) #Tile as given by the admin
    url = Column(String(2083)) #URL of the SOAP endpoint
    geoserver_url = Column(String(2083)) #Local geoserver url
    layer_name = Column(String(50)) #Store id for the layer as seen in the geoserver
    extents = Column(String(2083)) #Extents of the layer as defined by the geoserver

    def __init__(self,title,url,geoserver_url,layer_name,extents):
        """
        Constructor for the table
        """
        self.title = title
        self.url = url
        self.geoserver_url = geoserver_url
        self.layer_name = layer_name
        self.extents = extents