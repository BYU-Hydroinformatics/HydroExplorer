from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import sessionmaker
from .app import HydroExplorer as app
from sqlalchemy.sql import func

Base = declarative_base()


class Catalog(Base):
    __tablename__ = 'hydroservers'

    id = Column(Integer, primary_key=True)  # Record number.
    title = Column(String(50))  # Tile as given by the admin
    url = Column(String(2083))  # URL of the SOAP endpoint
    siteinfo = Column(JSON)
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())

    def __init__(self, title, url, siteinfo):
        self.title = title
        self.url = url
        self.siteinfo = siteinfo


class HISCatalog(Base):
    __tablename__ = 'hiscentrals'

    id = Column(Integer, primary_key=True)
    title = Column(String(50))
    url = Column(String(2083))

    def __init__(self, title, url):
        self.title = title
        self.url = url
