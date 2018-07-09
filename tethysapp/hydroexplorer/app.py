from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import PersistentStoreDatabaseSetting, SpatialDatasetServiceSetting


class HydroExplorer(TethysAppBase):

    # Note: The following properties can be modified through the Site Admin-->
    # Tethys Apps --> Installed Apps page
    name = 'Water Observations Data Integrator : HydroExplorer'
    index = 'hydroexplorer:home'
    icon = 'hydroexplorer/images/servir.png'
    package = 'hydroexplorer'
    root_url = 'hydroexplorer'
    color = '#004de6'
    description = 'Water Observations Data Integrator : HydroExplorer'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        UrlMap = url_map_maker(self.root_url)
        url_maps = (
            UrlMap(name='home',
                   url='hydroexplorer',
                   controller='hydroexplorer.controllers.home'),
            # Home Page controller. Responsible for generating a HTML elements for GLDAS, Climate Serv Modals.
            # It also finds the list of available hydroservers from
            # CUAHSI HIS central.
            UrlMap(name='add-server',
                   url='hydroexplorer/add-server',
                   controller='hydroexplorer.controllers.add_server'),
            # Create's a geoserver layer based on the HydroServer REST endpoint and
            # add's that HydroServer metadata to a persistant store
            UrlMap(name='add-central',
                   url='hydroexplorer/add-central',
                   controller='hydroexplorer.controllers.add_central'),
            # Create's a geoserver layer based on the HydroServer REST endpoint and
            # add's that HydroServer metadata to a persistant store
            UrlMap(name='details',
                   url='hydroexplorer/details',
                   controller='hydroexplorer.controllers.details'),
            # Generates the template for the Site Details page.
            UrlMap(name='rest-api',
                   url='hydroexplorer/rest-api',
                   controller='hydroexplorer.controllers.rest_api'),
            # Stores the timeseries json value as a session object for
            # a REST request.
            UrlMap(name='soap',
                   url='hydroexplorer/soap',
                   controller='hydroexplorer.controllers.soap'),
            # Create's a geoserver layer based on the HydroServer SOAP endpoint and add's
            # that HydroServer metadata to a persistant store
            UrlMap(name='soap-api',
                   url='hydroexplorer/soap-api',
                   controller='hydroexplorer.controllers.soap_api'),
            # Stores the timeseries json value as a session object for
            # a SOAP request.
            UrlMap(name='soap-var',
                   url='hydroexplorer/soap-var',
                   controller='hydroexplorer.controllers.soap_var'),
            # Stores the variable information from the Site Details
            # page for a SOAP request.
            UrlMap(name='catalog',
                   url='hydroexplorer/catalog',
                   controller='hydroexplorer.controllers.catalog'),
            # Returns a list of existing HydroServers in the local database
            UrlMap(name='catalogs',
                   url='hydroexplorer/catalogs',
                   controller='hydroexplorer.controllers.catalogs'),
            # Returns a list of existing Catalogs in the local database


            UrlMap(name='catalog-servers',
                   url='hydroexplorer/catalog/servers',
                   controller='hydroexplorer.controllers.catalog_servers'),

            UrlMap(name='delete',
                   url='hydroexplorer/delete',
                   controller='hydroexplorer.controllers.delete'),
            # Deletes a selected HydroServer from the local database
            UrlMap(name='his',
                   url='hydroexplorer/his',
                   controller='hydroexplorer.controllers.his'),
            # Returns a list of current HIS servers. This was created
            # for testing purposes, not used in the user interface.
            UrlMap(name='his-server',
                   url='hydroexplorer/his-server',
                   controller='hydroexplorer.controllers.get_his_server'),
            # Returns the selected HIS server from the select HIS
            # server modal.
            UrlMap(name='error',
                   url='hydroexplorer/error',
                   controller='hydroexplorer.controllers.error'),
            # The page that shows up whenever there is an error.
            UrlMap(name='create',
                   url='hydroexplorer/create',
                   controller='hydroexplorer.controllers.create'),
            # An empty controller. In case we ever want to build a
            # full-on hydroserver within the app.
            UrlMap(name='add-site',
                   url='hydroexplorer/add-site',
                   controller='hydroexplorer.controllers.add_site'),
            # A dummy controller. Again, in case we ever want to build
            # a full-scale hydroserver within tethys.
            UrlMap(name='datarods',
                   url='hydroexplorer/datarods',
                   controller='hydroexplorer.controllers.datarods'),
            # Takes the information from the GLDAS modal and returns a
            # timeseries plot
            UrlMap(name='cserv',
                   url='hydroexplorer/cserv',
                   controller='hydroexplorer.controllers.cserv'),
            # Takes the information from the Climate Serv modal and
            # generate a timeseries plot
            UrlMap(name='upload-shp',
                   url='hydroexplorer/upload-shp',
                   controller='hydroexplorer.controllers.upload_shp'),
            # Add a shapefile to the map as a geojson object

        )

        return url_maps

    def persistent_store_settings(self):
        ps_settings = (
            PersistentStoreDatabaseSetting(
                name='catalog_db',
                description='catalogs database',
                initializer='hydroexplorer.init_stores.init_catalog_db',
                required=True
            ),
        )

        return ps_settings

    def spatial_dataset_service_settings(self):
        sds_settings = (
            SpatialDatasetServiceSetting(
                name='primary_geoserver',
                description='spatial dataset service for app to use',
                engine=SpatialDatasetServiceSetting.GEOSERVER,
                required=True,
            ),
        )

        return sds_settings
