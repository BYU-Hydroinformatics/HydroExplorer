from sqlalchemy.orm import sessionmaker
from .model import Base, Catalog

#Initialize an empty database, if the database has not been created already.
def init_catalog_db(engine, first_time):
    Base.metadata.create_all(engine)

    if first_time:
        # Make session
        SessionMaker = sessionmaker(bind=engine)
        session = SessionMaker()

        ##Default Url
        hs_one = Catalog(title="DominicanRepublic",
                         url="http://worldwater.byu.edu/app/index.php/dr/services/cuahsi_1_1.asmx?WSDL",
                         geoserver_url="http://127.0.0.1:8181/geoserver/wms",layer_name="catalog:test",extents="{u'minx': -165.507222222222, u'miny': 30.81263, u'maxx': 34.8349, u'maxy': 64.5641666666667}")
        session.add(hs_one)
        session.commit()
        session.close()
