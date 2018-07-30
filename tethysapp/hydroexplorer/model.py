from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import sessionmaker
from .app import HydroExplorer as app

Base = declarative_base()


class Catalog(Base):
    __tablename__ = 'hydroservers'

    id = Column(Integer, primary_key=True)  # Record number.
    title = Column(String(50))  # Tile as given by the admin
    url = Column(String(2083))  # URL of the SOAP endpoint
    geoserver_url = Column(String(2083))  # Local geoserver url
    # Store id for the layer as seen in the geoserver
    layer_name = Column(String(50))
    # Extents of the layer as defined by the geoserver
    extents = Column(String(2083))
    siteinfo = Column(JSON)


    def __init__(self, title, url, geoserver_url, layer_name, extents, siteinfo):
        self.title = title
        self.url = url
        self.geoserver_url = geoserver_url
        self.layer_name = layer_name
        self.extents = extents
        self.siteinfo = siteinfo


class HISCatalog(Base):
    __tablename__ = 'hiscentrals'

    id = Column(Integer, primary_key=True)
    title = Column(String(50))
    url = Column(String(2083))

    def __init__(self, title, url):
        self.title = title
        self.url = url
