from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String
from sqlalchemy.orm import sessionmaker

from .app import ServirCatalog

engine = ServirCatalog.get_persistent_store_engine('catalog_db')
SessionMaker = sessionmaker(bind=engine)
Base = declarative_base()

class Catalog(Base):

    __tablename__ = 'hydroservers'

    # Table Columns

    id = Column(Integer, primary_key = True)
    title = Column(String(50))
    url = Column(String(2083))
    geoserver_url = Column(String(2083))
    layer_name = Column(String(50))
    extents = Column(String(2083))
    def __init__(self,title,url,geoserver_url,layer_name,extents):
        """
        Constructor for the table
        """
        self.title = title
        self.url = url
        self.geoserver_url = geoserver_url
        self.layer_name = layer_name
        self.extents = extents