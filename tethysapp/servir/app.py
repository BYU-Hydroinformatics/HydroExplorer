from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.stores import PersistentStore

class ServirCatalog(TethysAppBase):
    """
    Tethys app class for Servir Catalog.
    """

    name = 'Servir Water Observations Data Integrator'
    index = 'servir:home'
    icon = 'servir/images/servir.png'
    package = 'servir'
    root_url = 'servir'
    color = '#004de6'
    description = 'Place a brief description of your app here.'
    enable_feedback = False
    feedback_emails = []

        
    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (UrlMap(name='home',
                           url='servir',
                           controller='servir.controllers.home'),
                    UrlMap(name='add-server',
                           url='servir/add-server',
                           controller='servir.controllers.add_server'),
                    UrlMap(name='details',
                           url='servir/details',
                           controller='servir.controllers.details'),
                    UrlMap(name='rest-api',
                           url='servir/rest-api',
                           controller='servir.controllers.rest_api'),
                    UrlMap(name='soap',
                           url='servir/soap',
                           controller='servir.controllers.soap'),
                    UrlMap(name='soap-api',
                           url='servir/soap-api',
                           controller='servir.controllers.soap_api'),
                    UrlMap(name='soap-var',
                           url='servir/soap-var',
                           controller='servir.controllers.soap_var'),
                    UrlMap(name='catalog',
                           url='servir/catalog',
                           controller='servir.controllers.catalog'),
                    UrlMap(name='delete',
                           url='servir/delete',
                           controller='servir.controllers.delete'),
                    UrlMap(name='his',
                           url='servir/his',
                           controller='servir.controllers.his'),
                    UrlMap(name='his-server',
                           url='servir/his-server',
                           controller='servir.controllers.get_his_server'),
                    UrlMap(name='error',
                           url='servir/error',
                           controller='servir.controllers.error'),
                    UrlMap(name='create',
                           url='servir/create',
                           controller='servir.controllers.create'),
                    UrlMap(name='add-site',
                           url='servir/add-site',
                           controller='servir.controllers.add_site'),
                    UrlMap(name='datarods',
                           url='servir/datarods',
                           controller='servir.controllers.datarods'),
        )


        return url_maps

    def persistent_stores(self):
        """
        Add one or more persistent stores
        """
        stores = (PersistentStore(name='catalog_db',
                                  initializer='servir.init_stores.init_catalog_db'
                                  ),
                  )

        return stores