from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.stores import PersistentStore

class ServirCatalog(TethysAppBase):
    """
    Tethys app class for Servir Catalog.
    """

    #Note: The following properties can be modified through the Site Admin--> Tethys Apps --> Installed Apps page
    name = 'Servir Water Observations Data Integrator'
    index = 'servir:home'
    icon = 'servir/images/servir.png'
    package = 'servir'
    root_url = 'servir'
    color = '#004de6' #Change this to change the primary color of the app
    description = 'Place a brief description of your app here.' #Change this to change the description of the app
    enable_feedback = False
    feedback_emails = []

        
    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        #See controller.py for the relevant functions
        url_maps = (UrlMap(name='home',
                           url='servir',
                           controller='servir.controllers.home'), #Home Page controller. Responsible for generating a HTML elements for GLDAS, Climate Serv Modals. It also finds the list of available hydroservers from CUAHSI HIS central.
                    UrlMap(name='add-server',
                           url='servir/add-server',
                           controller='servir.controllers.add_server'),#Create's a geoserver layer based on the HydroServer REST endpoint and add's that HydroServer metadata to a persistant store
                    UrlMap(name='details',
                           url='servir/details',
                           controller='servir.controllers.details'),#Generates the template for the Site Details page.
                    UrlMap(name='rest-api',
                           url='servir/rest-api',
                           controller='servir.controllers.rest_api'),#Stores the timeseries json value as a session object for a REST request.
                    UrlMap(name='soap',
                           url='servir/soap',
                           controller='servir.controllers.soap'),#Create's a geoserver layer based on the HydroServer SOAP endpoint and add's that HydroServer metadata to a persistant store
                    UrlMap(name='soap-api',
                           url='servir/soap-api',
                           controller='servir.controllers.soap_api'),#Stores the timeseries json value as a session object for a SOAP request.
                    UrlMap(name='soap-var',
                           url='servir/soap-var',
                           controller='servir.controllers.soap_var'),#Stores the variable information from the Site Details page for a SOAP request.
                    UrlMap(name='catalog',
                           url='servir/catalog',
                           controller='servir.controllers.catalog'),#Returns a list of existing HydroServers in the local database
                    UrlMap(name='delete',
                           url='servir/delete',
                           controller='servir.controllers.delete'),#Deletes a selected HydroServer from the local database
                    UrlMap(name='his',
                           url='servir/his',
                           controller='servir.controllers.his'),#Returns a list of current HIS servers. This was created for testing purposes, not used in the user interface.
                    UrlMap(name='his-server',
                           url='servir/his-server',
                           controller='servir.controllers.get_his_server'),#Returns the selected HIS server from the select HIS server modal.
                    UrlMap(name='error',
                           url='servir/error',
                           controller='servir.controllers.error'),#The page that shows up whenever there is an error.
                    UrlMap(name='create',
                           url='servir/create',
                           controller='servir.controllers.create'),#An empty controller. In case we ever want to build a full-on hydroserver within the app.
                    UrlMap(name='add-site',
                           url='servir/add-site',
                           controller='servir.controllers.add_site'),#A dummy controller. Again, in case we ever want to build a full-scale hydroserver within tethys.
                    UrlMap(name='datarods',
                           url='servir/datarods',
                           controller='servir.controllers.datarods'),#Takes the information from the GLDAS modal and returns a timeseries plot
                    UrlMap(name='cserv',
                           url='servir/cserv',
                           controller='servir.controllers.cserv'),#Takes the information from the Climate Serv modal and generate a timeseries plot
                    UrlMap(name='upload-shp',
                           url='servir/upload-shp',
                           controller='servir.controllers.upload_shp'),#Add a shapefile to the map as a geojson object

        )


        return url_maps

    #Declaring the database class
    def persistent_stores(self):
        """
        Add one or more persistent stores
        """
        stores = (PersistentStore(name='catalog_db', #Name of the persistent store
                                  initializer='servir.init_stores.init_catalog_db' #Location of the persistent store initialization function. See init_stores.py
                                  ),
                  )

        return stores