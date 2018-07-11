import xmltodict
import json
import urllib2
import time
import calendar
import logging
import unicodedata
import ast
import shapely.geometry  # Get the bounds of a given geometry
import shapely.ops
import os
import tempfile
import shutil
import sys
import xml.etree.ElementTree as ET

from utilities import *
from json import dumps, loads
from datetime import datetime, timedelta
from xml.etree.ElementTree import XML, fromstring, tostring
from suds.client import Client  # For parsing WaterML/XML

from tethys_sdk.gizmos import TimeSeries, SelectInput, DatePicker, TextInput, GoogleMapView
from tethys_sdk.services import get_spatial_dataset_engine, list_spatial_dataset_engines

from django.conf import settings
from django.core import serializers
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required


from pyproj import Proj, transform  # Reprojecting/Transforming coordinates
from owslib.waterml.wml11 import WaterML_1_1 as wml11

from .app import HydroExplorer as app
from .model import Catalog, HISCatalog

Persistent_Store_Name = 'catalog_db'

logging.getLogger('suds.client').setLevel(logging.CRITICAL)

spatial_dataset_engine = app.get_spatial_dataset_service(
    'primary_geoserver', as_engine=True)


def home(request):
    """
    Controller for the app home page.
    """

    # Start the GLDAS code
    # Generate the dropdown options for GLDAS. See utilities.py for
    # gen_gldas_dropdown function
    gldas_dropdown = gen_gldas_dropdown()
    select_gldas_variable = SelectInput(display_text='Select Variable',
                                        name="select_gldas_var", multiple=False,
                                        options=gldas_dropdown)  # Dropdown for selecting the GLDAS Variable

    # Get the GLDAS date range. See utilities.py for get_gldas_range function
    gldas_dates = get_gldas_range()

    start_date = DatePicker(name='start_date',
                            display_text='Start Date',
                            autoclose=True,
                            format='yyyy-mm-dd',
                            start_view='month',
                            today_button=True,
                            initial=gldas_dates["start"],
                            start_date=gldas_dates["start"],
                            end_date=gldas_dates["end"])  # Datepicker object for selecting the GLDAS start date

    end_date = DatePicker(name='end_date',
                          display_text='End Date',
                          autoclose=True,
                          format='yyyy-mm-dd',
                          start_view='month',
                          today_button=True,
                          initial=gldas_dates["end"],
                          start_date=gldas_dates["start"],
                          end_date=gldas_dates["end"])  # Datepicker object for selecting the GLDAS end date

    # End of GLDAS code segment

    # Start Climate Serv code
    data_type_options = [["CHIRPS Precipitation", "0|CHIRPS Precipitation(mm/day)"],
                         ["IMERG 1 Day", "26|IMERG 1 Day(1 mm/day)"],
                         ["Seasonal Forecast", "6|Seasonal Forecast"]
                         ]  # Climate Serv Data Type Options
    operation_type_options = [["Max", "0|max"],
                              ["Min", "1|min"],
                              ["Average", "5|avg"]
                              ]  # Climate Serv Operation Type options
    # Climate Serv interval type options
    interval_type_options = [["Daily", "0"]]

    select_data_type = SelectInput(display_text='Select a data type', name='cs_data_type',
                                   multiple=False, options=data_type_options)  # Dropdown object for the select data type
    select_operation_type = SelectInput(display_text='Select a operation type',
                                        name='cs_operation_type', multiple=False,
                                        options=operation_type_options)  # Dropdown for select operation type
    select_interval_type = SelectInput(display_text='Select a date interval',
                                       name='cs_interval_type', multiple=False,
                                       options=interval_type_options)  # Dropdown for select interval type
    select_forecast_variable = SelectInput(display_text='Select a variable',
                                           name='cs_forecast_variable', multiple=False,
                                           options=[("Precipitation", "Precipitation"),
                                                    ("Temperature", "Temperature")])  # A dropdown object for selecting the forecast variable

    # Get the seasonal forecast range. See utilities.py.
    seasonal_forecast_range = get_sf_range()
    today = datetime.today().strftime("%m/%d/%Y")

    forecast_start = DatePicker(name='forecast_start',
                                display_text='Start Date',
                                autoclose=True,
                                format='mm/dd/yyyy',
                                start_view='month',
                                today_button=True,
                                initial="01/10/2016")  # Datepicker object for Climate Serv forecast start date

    forecast_end = DatePicker(name='forecast_end',
                              display_text='End Date',
                              autoclose=True,
                              format='mm/dd/yyyy',
                              start_view='month',
                              today_button=True,
                              initial="01/20/2016")  # Datepicker object for Climate Serv forecast end date

    seasonal_forecast_start = DatePicker(name='seasonal_forecast_start',
                                         display_text='Start Date',
                                         autoclose=True,
                                         format='mm/dd/yyyy',
                                         start_view='month',
                                         today_button=True,
                                         initial=today,
                                         start_date=seasonal_forecast_range[
                                             "start"],
                                         end_date=seasonal_forecast_range["end"])  # Datepicker object for Climate Serv seasonal forecast start date

    seasonal_forecast_end = DatePicker(name='seasonal_forecast_end',
                                       display_text='End Date',
                                       autoclose=True,
                                       format='mm/dd/yyyy',
                                       start_view='month',
                                       today_button=True,
                                       initial=today,
                                       start_date=seasonal_forecast_range[
                                           "start"],
                                       end_date=seasonal_forecast_range["end"])  # Datepicker object for Climate Serv seasonal forecast end date
    # End Climate Serv code block

    # Django context variables that will be used in home.html
    context = {
        "select_gldas_variable": select_gldas_variable,
        "start_date": start_date,
        "end_date": end_date,
        "select_data_type": select_data_type,
        "select_operation_type": select_operation_type,
        "select_interval_type": select_interval_type,
        "forecast_start": forecast_start,
        "forecast_end": forecast_end,
        "select_forecast_variable": select_forecast_variable,
        "seasonal_forecast_start": seasonal_forecast_start,
        "seasonal_forecast_end": seasonal_forecast_end}

    return render(request, 'hydroexplorer/home.html', context)

# No real use for this controller at the moment


def create(request):
    context = {}
    return render(request, 'hydroexplorer/create.html', context)


def cserv(request):
    """
        Controller for generating timeseries plot through the Climate Serv API.
    """

    # Defining all the parameters that will be used to make the Climate Serv
    # API call
    data_type = request.GET['cs_data_type']
    data_type = data_type.split("|")
    data_type_int = data_type[0]
    data_type_title = data_type[1]
    geometry = request.GET['cserv_lat_lon']

    operation_type = request.GET['cs_operation_type']
    operation_type = operation_type.split("|")
    operation_type_int = operation_type[0]
    operation_type_var = operation_type[1]
    interval_type = request.GET['cs_interval_type']
    begin_data = request.GET['forecast_start']
    end_data = request.GET['forecast_end']
    data_type_category = "default"

    # The seasonal forecast requires a couple of additional variables. This
    # process runs if seasonal forecast is selected.
    if data_type_title == "Seasonal Forecast":
        model_ensemble = request.GET['cs_model_ensemble']
        forecast_variable = request.GET['cs_forecast_variable']
        # Get the datatype number from the model ensemble and forecast
        # variable. See utlities.py.
        data_type_info = get_climate_scenario(
            model_ensemble, forecast_variable)
        datatype = data_type_info
        data_type_title = data_type[1] + ' ' + str(forecast_variable)
        begin_data = request.GET['seasonal_forecast_start']
        end_data = request.GET['seasonal_forecast_end']
        data_type_category = "ClimateModel"
    else:
        datatype = data_type_int

    # Submit a request to the Climate Serv API based on the paramters that
    # were defined earlier
    submit_data_request = "http://chirps.nsstc.nasa.gov/chirps/submitDataRequest/?begintime={0}&endtime={1}&datatype={2}&operationtype={3}&intervaltype={4}&geometry={5}".format(
        begin_data, end_data, datatype, operation_type_int, interval_type, geometry)
    # submit_data_request = urllib2.quote(submit_data_request,safe=':/-()&=,?[]"')
    submit_response = urllib2.urlopen(submit_data_request)
    submit_response_data = submit_response.read()
    job_id = str(submit_response_data)
    job_id = job_id.strip('[]"')  # Retrieving the jobid from the request

    # Now getting the data with the jobib
    actual_data_url = "http://chirps.nsstc.nasa.gov/chirps/getDataFromRequest/?id={0}".format(
        job_id)

    # I have no explanation for why this delay is necessary, but without this
    # the code will break.
    time.sleep(3)
    # Generate a timeseries from the data url
    graph = process_job_id(actual_data_url, operation_type_var)

    timeseries_plot = TimeSeries(
        height='400px',
        width='100%',
        engine='highcharts',
        title=data_type_title,
        y_axis_title=data_type_title,
        y_axis_units=str(operation_type_var),
        series=[{
            'name': data_type_title,
            'data': graph
        }]
    )  # Timeseries object for the Climate Serv request

    context = {"timeseries_plot": timeseries_plot}

    return render(request, 'hydroexplorer/cserv.html', context)


def datarods(request):
    """
        Controller for generating timeseries plot through the Datarods API.
    """
    context = {}  # Empty context, so that I can redirect the page in case of errors.

    # Getting the POST request data with the variable info, date range, and
    # point lat lon.
    variable = request.GET['select_gldas_var']
    variable = variable.split('|')
    var_id = variable[0]
    var_name = variable[1]
    var_units = variable[2]
    start_date = request.GET['start_date']
    end_date = request.GET['end_date']
    start_str = str(start_date) + 'T00'
    end_str = str(end_date) + 'T23'
    latlon = request.GET['gldas-lat-lon']
    latlon = latlon.split(',')
    lon, lat = float(latlon[0]), float(latlon[1])
    lon = round(lon, 2)
    lat = round(lat, 2)
    coords_string = str(lon) + ", " + str(lat)

    # Geocoding to get the location name. See utilities.py.
    location_name = get_loc_name(lat, lon)
    # Since some places have unique and interesting characters. It is
    # important to encode and then decode them.
    location_name = location_name.decode("utf-8")
    coords_str_formatted = str(lat) + "," + str(lon)
    # GLDAS request url
    gldas_url = "http://hydro1.sci.gsfc.nasa.gov/daac-bin/access/timeseries.cgi?variable=GLDAS:GLDAS_NOAH025_3H.001:{0}&type=asc2&location=GEOM:POINT({1})&startDate={2}&endDate={3}".format(
        var_id, coords_string, start_str, end_str)
    # Using safe as the url as several special characters
    gldas_url = urllib2.quote(gldas_url, safe=':/-()&=,?')
    try:
        # Retrieve the data and creating a timeseries object from the request.
        # See utilities.py.
        gldas_response = urllib2.urlopen(gldas_url)
        gldas_data = gldas_response.read()
        parsed_gldas = parse_gldas_data(gldas_data)

        timeseries_plot = TimeSeries(
            height='400px',
            width='100%',
            engine='highcharts',
            title=var_name + " at " + location_name,
            y_axis_title=str(var_name),
            y_axis_units=var_units,
            series=[{
                'name': coords_str_formatted,
                'data': parsed_gldas
            }]
        )  # Timeseries object for the GLDAS request

        context = {"timeseries_plot": timeseries_plot}
    except Exception as e:
        # Return an error for any exceptions.
        error_message = "There was a problem retrieving data from the NASA Server"
        context = {"error_message": error_message}

    return render(request, 'hydroexplorer/datarods.html', context)

# A use-case scenario for making an in-built hydroserver within Tethys.


def add_site(request):
    select_source = SelectInput(display_text='Select Source',
                                name='select-source',
                                multiple=False,
                                options=[('One', '1'), ('Two', '2'), ('Three', '3')])
    select_site_type = SelectInput(display_text='Select Site Type',
                                   name='select-site-type',
                                   multiple=False,
                                   options=[('Four', '4'), ('Five', '5'), ('Six', '6')])
    select_vertical_datum = SelectInput(display_text='Select Vertical Datum',
                                        name='select-vertical-datum',
                                        multiple=False,
                                        options=[('MSL', 'MSL'), ('NAVD88', 'NAVDD88'), ('NGVD29', 'NGVD29'), ('Something', 'Something'), ('Unknown', 'Unknown')])
    select_spatial_reference = SelectInput(display_text='Select Spatial Reference',
                                           name='select-spatial-reference',
                                           multiple=False,
                                           options=[('WGS84', 'WGS84'), ('NAD27', 'NAD27')])
    google_map_view = GoogleMapView(height='400px',
                                    width='100%',
                                    maps_api_key='S0mEaPIk3y',
                                    drawing_types_enabled=['POINTS'])
    if request.POST and 'site-name' in request.POST:
        site_name = request.POST['site-name']

    context = {"select_source": select_source, "select_site_type": select_site_type, "select_vertical_datum": select_vertical_datum,
               "select_spatial_reference": select_spatial_reference, "google_map_view": google_map_view}
    return render(request, 'hydroexplorer/addsite.html', context)

# Controller for passing the selected HIS server to the Add SOAP server modal.


def get_his_server(request):
    server = {}
    if request.is_ajax() and request.method == 'POST':
        url = request.POST['select_server']
        server['url'] = url
    return JsonResponse(server)

# A test to check for good hydroservers. Not used in the user interface


def his(request):
    list = {}
    hs_list = []
    error_list = []
    logging.getLogger('suds.client').setLevel(logging.CRITICAL)
    his_url = "http://hiscentral.cuahsi.org/webservices/hiscentral.asmx?WSDL"
    client = Client(his_url)
    searchable_concepts = client.service.GetSearchableConcepts()
    service_info = client.service.GetWaterOneFlowServiceInfo()
    # print service_info.ServiceInfo[0].servURL
    services = service_info.ServiceInfo
    for i in services:
        hs = {}
        url = i.servURL
        try:
            print "Testing %s" % (url)
            url_client = Client(url)
            hs['url'] = url
            hs_list.append(hs)
            print "%s Works" % (url)
        except Exception as e:
            print e
            hs['url'] = url
            print "%s Failed" % (url)
            error_list.append(hs)
        list['servers'] = hs_list
        list['errors'] = error_list

    context = {"hs_list": hs_list, "error_list": error_list}

    return render(request, 'hydroexplorer/his.html', context)


def catalog(request):
    '''
    Controller for retrieving the list of available HydroServers in the local database.
    '''
    list = {}

    SessionMaker = app.get_persistent_store_database(
        Persistent_Store_Name, as_sessionmaker=True)
    session = SessionMaker()  # Initiate a session

    # Query DB for hydroservers
    hydroservers = session.query(Catalog).all()

    hs_list = []
    for server in hydroservers:
        layer_obj = {}
        layer_obj["geoserver_url"] = server.geoserver_url
        layer_obj["title"] = server.title
        layer_obj["url"] = server.url
        layer_obj["layer_name"] = server.layer_name
        if server.extents:
            json_encoded = ast.literal_eval(server.extents)
        else:
            json_encoded = ""
        layer_obj["extents"] = json_encoded

        hs_list.append(layer_obj)
    # A json list object with the HydroServer metadata. This object will be
    # used to add layers to the catalog table on the homepage.
    list["hydroserver"] = hs_list

    return JsonResponse(list)


def catalogs(request):

    SessionMaker = app.get_persistent_store_database(
        Persistent_Store_Name, as_sessionmaker=True)
    session = SessionMaker()

    catalogs = session.query(HISCatalog).all()

    hydroCatalogs = list(
        map(lambda x: (x.title, x.url), catalogs))

    his_catalogs = SelectInput(
        name="select_catalog",
        display_text='Select HIS Catalog',
        multiple=False,
        options=hydroCatalogs,
        select2_options={'placeholder': 'Select a Catalog'})

    return render(request, 'hydroexplorer/modals/helpers/catalog.html', {'his_catalogs': his_catalogs})


def catalog_servers(request):

    # Connecting to the CUAHSI HIS central to
    # retrieve all the avaialable HydroServers.
    url = request.POST['url']
    his_servers = []
    his_url = url + "?WSDL"
    client = Client(his_url)
    service_info = client.service.GetWaterOneFlowServiceInfo()
    services = service_info.ServiceInfo
    for i in services:
        try:
            url = i.servURL.encode('utf-8')
            title = i.Title.encode('utf-8')
            organization = i.organization.encode('utf-8')
            variable_str = "Title: %s, Organization: %s" % (
                title, organization)
            his_servers.append([variable_str, url])
        except Exception as e:
            print e

    select_his_server = SelectInput(display_text='Select HIS Server',
                                    name="select_server", multiple=False,
                                    options=his_servers)

    return render(request, 'hydroexplorer/modals/helpers/catalog.html', {"select_his_server": select_his_server})


def delete(request):
    '''
    Controller for deleting a user selected HydroServer from the local database
    '''
    list = {}

    SessionMaker = app.get_persistent_store_database(
        Persistent_Store_Name, as_sessionmaker=True)
    session = SessionMaker()

    # Query DB for hydroservers
    if request.is_ajax() and request.method == 'POST':
        title = request.POST['server']
        spatial_dataset_engine = app.get_spatial_dataset_service(
            'primary_geoserver', as_engine=True)
        store_string = "catalog" + ":" + str(title)
        # Deleting the layer on geoserver
        spatial_dataset_engine.delete_layer(layer_id=store_string, purge=True)
        # Deleting the store on geoserver
        spatial_dataset_engine.delete_store(store_id=store_string, purge=True)
        hydroservers = session.query(Catalog).filter(Catalog.title == title).delete(
            synchronize_session='evaluate')  # Deleting the record from the local catalog
        session.commit()
        session.close()

        # spatial_dataset_engine.delete_store(title,purge=True,debug=True)
        # Returning the deleted title. To let the user know that the particular
        # title is deleted.
        list["title"] = title
    return JsonResponse(list)



def del_catalog(request):
    list = {}

    SessionMaker = app.get_persistent_store_database(
        Persistent_Store_Name, as_sessionmaker=True)
    session = SessionMaker()

    # Query DB for hydroservers
    if request.is_ajax() and request.method == 'POST':
        title = request.POST['server']
        
        catalogs = session.query(HISCatalog).filter(HISCatalog.title == title).delete(
            synchronize_session='evaluate')  # Deleting the record from the local catalog
        session.commit()
        session.close()

        # Returning the deleted title. To let the user know that the particular
        # title is deleted.
        list["title"] = title
    return JsonResponse(list)

# Controller for adding a REST endpoint. As of today, this controller is
# not being used in the front end. Just leaving it here for future
# reference.


def add_server(request):
    return_obj = {}
    geo_url = spatial_dataset_engine.endpoint.replace(
        '/geoserver/rest', '') + "/geoserver/rest/"

    if request.is_ajax() and request.method == 'POST':
        url = request.POST['hs-url']
        title = request.POST['hs-title']
        title = title.replace(" ", "")
        if url.endswith('/'):
            url = url[:-1]

        #cuahsi_validation_str = "cuahsi_1_1.asmx"
        # if cuahsi_validation_str in url:
        get_sites = url + "/GetSitesObject"
        sites_object = parseSites(get_sites)
        shapefile_object = genShapeFile(sites_object, title, url)

        geoserver_rest_url = spatial_dataset_engine.endpoint.replace(
            '/geoserver/rest', '') + "/geoserver/wms"
        return_obj['rest_url'] = geoserver_rest_url
        return_obj['wms'] = shapefile_object["layer"]
        return_obj['bounds'] = shapefile_object["extents"]
        extents_string = str(shapefile_object["extents"])
        return_obj['title'] = title
        return_obj['url'] = url
        return_obj['status'] = "true"

        SessionMaker = app.get_persistent_store_database(
            Persistent_Store_Name, as_sessionmaker=True)
        session = SessionMaker()
        hs_one = Catalog(title=title,
                         url=url, geoserver_url=geoserver_rest_url, layer_name=shapefile_object["layer"], extents=extents_string)
        session.add(hs_one)
        session.commit()
        session.close()
    else:
        return_obj[
            'message'] = 'This request can only be made through a "POST" AJAX call.'

    return JsonResponse(return_obj)


def add_central(request):

    return_obj = {}

    if request.is_ajax() and request.method == 'POST':
        url = request.POST['url']
        title = request.POST['title']

        if url.endswith('/'):
            url = url[:-1]

        if(checkCentral(url)):
            return_obj['message'] = 'Valid HIS Central Found'
            return_obj['status'] = True
            # Add to the database

            SessionMaker = app.get_persistent_store_database(
                Persistent_Store_Name, as_sessionmaker=True)
            session = SessionMaker()
            hs_one = HISCatalog(title=title, url=url)
            session.add(hs_one)
            session.commit()
            session.close()
        else:
            return_obj['message'] = 'Not a valid HIS Central Catalog'
            return_obj['status'] = False
    else:
        return_obj[
            'message'] = 'This request can only be made through a "POST" AJAX call.'
        return_obj['status'] = False

    return JsonResponse(return_obj)


def soap(request):
    '''
    Controller for adding a SOAP endpoint
    '''
    return_obj = {}
    if request.is_ajax() and request.method == 'POST':

        logging.getLogger('suds.client').setLevel(logging.CRITICAL)

        geo_url = spatial_dataset_engine.endpoint.replace(
            '/geoserver/rest', '') + "/geoserver/rest/"

        # Defining variables based on the POST request
        url = request.POST['soap-url']
        title = request.POST['soap-title']
        title = title.replace(" ", "")
        # Getting the current map extent
        true_extent = request.POST.get('extent')

        client = Client(url)  # Connecting to the endpoint using SUDS

        # True Extent is on and necessary if the user is trying to add USGS or
        # some of the bigger HydroServers.
        if true_extent == 'on':
            extent_value = request.POST['extent_val']
            return_obj['zoom'] = 'true'
            return_obj['level'] = extent_value
            ext_list = extent_value.split(',')
            # Reprojecting the coordinates from 3857 to 4326 using pyproj
            inProj = Proj(init='epsg:3857')
            outProj = Proj(init='epsg:4326')
            minx, miny = ext_list[0], ext_list[1]
            maxx, maxy = ext_list[2], ext_list[3]
            x1, y1 = transform(inProj, outProj, minx, miny)
            x2, y2 = transform(inProj, outProj, maxx, maxy)
            bbox = client.service.GetSitesByBoxObject(
                x1, y1, x2, y2, '1', '')  # Get Sites by bounding box using suds
            # Creating a sites object from the endpoint. This site object will
            # be used to generate the geoserver layer. See utilities.py.
            wml_sites = parseWML(bbox)

            # Generating a shapefile from the sites object and title. Then add
            # it to the local geoserver. See utilities.py.
            shapefile_object = genShapeFile(wml_sites, title,  url)
            geoserver_rest_url = spatial_dataset_engine.endpoint.replace(
                '/geoserver/rest', '') + "/geoserver/wms"

            # The json response will have the metadata information about the
            # geoserver layer
            return_obj['rest_url'] = geoserver_rest_url
            return_obj['wms'] = shapefile_object["layer"]
            return_obj['bounds'] = shapefile_object["extents"]
            extents_string = str(shapefile_object["extents"])

            # extents_dict = xmltodict.parse(extents_string)
            # extents_json_object = json.dumps(extents_dict)
            # extents_json = json.loads(extents_json_object)

            return_obj['title'] = title
            return_obj['url'] = url
            return_obj['status'] = "true"
            SessionMaker = app.get_persistent_store_database(
                Persistent_Store_Name, as_sessionmaker=True)
            session = SessionMaker()
            hs_one = Catalog(title=title,
                             url=url, geoserver_url=geoserver_rest_url, layer_name=shapefile_object[
                                 "layer"],
                             extents=extents_string)  # Adding all the HydroServer geoserver layer metadata to the local database
            session.add(hs_one)
            session.commit()
            session.close()

        else:
            return_obj['zoom'] = 'false'
            # Get a list of all the sites and their respective lat lon.
            sites = client.service.GetSites('[:]')
            sites_dict = xmltodict.parse(sites)
            sites_json_object = json.dumps(sites_dict)
            sites_json = json.loads(sites_json_object)
            # Parsing the sites and creating a sites object. See utilities.py
            sites_object = parseJSON(sites_json)
            # Generate a shapefile from the sites object and title. Then add it
            # to the geoserver.
            shapefile_object = genShapeFile(sites_object, title, url)

            geoserver_rest_url = spatial_dataset_engine.endpoint.replace(
                '/geoserver/rest', '') + "/geoserver/wms"

            # The json response will have the metadata information about the
            # geoserver layer
            return_obj['rest_url'] = geoserver_rest_url
            return_obj['wms'] = shapefile_object["layer"]
            return_obj['bounds'] = shapefile_object["extents"]
            extents_string = str(shapefile_object["extents"])
            return_obj['title'] = title
            return_obj['url'] = url
            return_obj['status'] = "true"

            SessionMaker = app.get_persistent_store_database(
                Persistent_Store_Name, as_sessionmaker=True)
            session = SessionMaker()
            hs_one = Catalog(title=title,
                             url=url, geoserver_url=geoserver_rest_url, layer_name=shapefile_object["layer"], extents=extents_string)  # Adding the HydroServer geosever layer metadata to the local database
            session.add(hs_one)
            session.commit()
            session.close()

    else:
        return_obj[
            'message'] = 'This request can only be made through a "POST" AJAX call.'

    return JsonResponse(return_obj)


def error(request):
    context = {}
    return render(request, 'hydroexplorer/error.html', context)


def details(request):
    # Defining the variables for site name, site code, network and hydroserver
    # url.
    site_name = request.GET['sitename']
    site_code = request.GET['sitecode']
    network = request.GET['network']
    hs_url = request.GET['hsurl']
    hidenav = request.GET['hidenav']
    service = request.GET['service']
    rest = None
    soap = None
    error_message = None

    # REST not really supported. I wont explain this code.
    if service == 'REST':
        if hs_url.endswith(''):
            hs_url = hs_url + "/"
        site_object = network + ":" + site_code
        rest = service
        get_site_info_url = hs_url + "GetSiteInfoObject?site=" + site_object
        site_info_response = urllib2.urlopen(get_site_info_url)
        site_info_data = site_info_response.read()
        site_info_dict = xmltodict.parse(site_info_data)
        site_info_json_object = json.dumps(site_info_dict)
        site_info_json = json.loads(site_info_json_object)

        start_date = "00-00-00"
        # variable_series[0]['variableTimeInterval']['beginDateTime'][:-9]

        end_date = "3000-01-01"
        # variable_series[0]['variableTimeInterval']['endDateTime'][:-9]

        site_values_url = hs_url + "GetValuesForASiteObject?site=" + \
            site_object + "&startDate=" + start_date + "&endDate=" + end_date

        site_values_response = urllib2.urlopen(site_values_url)
        site_values_data = site_values_response.read()
        xml_str = str(site_values_data)
        site_values_dict = xmltodict.parse(xml_str)
        site_values_json_object = json.dumps(site_values_dict)
        site_values_json = json.loads(site_values_json_object)

        times_series = site_values_json['timeSeriesResponse']['timeSeries']

        graphs = []
        nodata_message = None
        if type(times_series) is list:
            for i in times_series:
                if i['values'] is not None:
                    graph_json = {}
                    graph_json["variable"] = i['variable']['variableName']
                    graph_json["unit"] = i['variable'][
                        'unit']['unitAbbreviation']
                    graph_json["title"] = site_name + \
                        ':' + i['variable']['variableName']
                    for j in i['values']:
                        data_values = []
                        if j == "value":
                            if type((i['values']['value'])) is list:
                                for k in i['values']['value']:
                                    time = k['@dateTimeUTC']
                                    time1 = time.replace("T", "-")
                                    time_split = time1.split("-")
                                    year = int(time_split[0])
                                    month = int(time_split[1])
                                    day = int(time_split[2])
                                    hour_minute = time_split[3].split(":")
                                    hour = int(hour_minute[0])
                                    minute = int(hour_minute[1])
                                    value = float(str(k['#text']))
                                    date_string = datetime(
                                        year, month, day, hour, minute)
                                    time_stamp = calendar.timegm(
                                        date_string.utctimetuple()) * 1000
                                    data_values.append([time_stamp, value])
                                    data_values.sort()
                                graph_json["values"] = data_values
                            else:
                                time = i['values']['value']['@dateTimeUTC']
                                time1 = time.replace("T", "-")
                                time_split = time1.split("-")
                                year = int(time_split[0])
                                month = int(time_split[1])
                                day = int(time_split[2])
                                hour_minute = time_split[3].split(":")
                                hour = int(hour_minute[0])
                                minute = int(hour_minute[1])
                                value = float(
                                    str(i['values']['value']['#text']))
                                date_string = datetime(
                                    year, month, day, hour, minute)
                                time_stamp = calendar.timegm(
                                    date_string.utctimetuple()) * 1000
                                data_values.append([time_stamp, value])
                                data_values.sort()
                                graph_json["values"] = data_values
                    graphs.append(graph_json)
        else:
            if times_series['values'] is not None:
                graph_json = {}
                graph_json["variable"] = times_series[
                    'variable']['variableName']
                graph_json["unit"] = times_series[
                    'variable']['unit']['unitAbbreviation']
                graph_json["title"] = site_name + ':' + \
                    times_series['variable']['variableName']
                for j in times_series['values']:
                    data_values = []
                    if j == "value":
                        if type((times_series['values']['value'])) is list:
                            for k in times_series['values']['value']:
                                time = k['@dateTimeUTC']
                                time1 = time.replace("T", "-")
                                time_split = time1.split("-")
                                year = int(time_split[0])
                                month = int(time_split[1])
                                day = int(time_split[2])
                                hour_minute = time_split[3].split(":")
                                hour = int(hour_minute[0])
                                minute = int(hour_minute[1])
                                value = float(str(k['#text']))
                                date_string = datetime(
                                    year, month, day, hour, minute)
                                time_stamp = calendar.timegm(
                                    date_string.utctimetuple()) * 1000
                                data_values.append([time_stamp, value])
                                data_values.sort()
                            graph_json["values"] = data_values
                        else:
                            time = times_series['values'][
                                'value']['@dateTimeUTC']
                            time1 = time.replace("T", "-")
                            time_split = time1.split("-")
                            year = int(time_split[0])
                            month = int(time_split[1])
                            day = int(time_split[2])
                            hour_minute = time_split[3].split(":")
                            hour = int(hour_minute[0])
                            minute = int(hour_minute[1])
                            value = float(
                                str(times_series['values']['value']['#text']))
                            date_string = datetime(
                                year, month, day, hour, minute)
                            time_stamp = calendar.timegm(
                                date_string.utctimetuple()) * 1000
                            data_values.append([time_stamp, value])
                            data_values.sort()
                            graph_json["values"] = data_values
                graphs.append(graph_json)
            else:
                nodata_message = "There is no data for this Site"
                context = {"nodate_message": nodata_message, "site_name": site_name,
                           "site_code": site_code, "service": service}
                return render(request, 'hydroexplorer/error.html', context)

        graphs_object = {}
        graphs_object["graph"] = graphs
        graph_variables = []
        for var in graphs_object["graph"]:
            graph_variables.append([var["variable"], var["variable"]])

        select_variable = SelectInput(
            display_text='Select variable', name="select_var", multiple=False, options=graph_variables)
        select_soap_variable = []

        json.JSONEncoder.default = lambda self, obj: (
            obj.isoformat() if isinstance(obj, datetime) else None)
        request.session['graphs_object'] = graphs_object
        soap_obj = {}
        t_now = datetime.now()
        start_date = {}
        end_date = {}

    if service == 'SOAP':
        soap_obj = {}  # soap_obj json dictionary is used so that part of the important metadata can be stored as a session object
        soap = service
        soap_obj["url"] = hs_url

        client = Client(hs_url)  # Connecting to the HydroServer via suds
        client.set_options(port='WaterOneFlow')
        site_desc = network + ":" + site_code
        soap_obj["site"] = site_desc
        soap_obj["network"] = network
        site_info = client.service.GetSiteInfo(site_desc)  # Get site info
        # Encoding is necessary for making sure that this thing works for sites
        # with weird characters

        site_info = site_info.encode('utf-8')
        # Converting xml2dict to make it easier to parse
        info_dict = xmltodict.parse(site_info)
        # Converting the dict to a json object
        info_json_object = json.dumps(info_dict)
        info_json = json.loads(info_json_object)
        site_variables = []
        site_object_info = info_json['sitesResponse']['site']['seriesCatalog']

        # This exception was necessary as there were some sites with no data
        try:
            site_object = info_json['sitesResponse'][
                'site']['seriesCatalog']['series']
        except KeyError:
            error_message = "Site Details do not exist"
            context = {"site_name": site_name, "site_code": site_code,
                       "service": service, "error_message": error_message}
            return render(request, 'hydroexplorer/error.html', context)
        graph_variables = []  # List for storing all avaiable variables
        var_json = []  # List for storing the variable metadata such as the date range for the data for that variable

        # Check if there are multiple variables in the selected site
        if type(site_object) is list:
            count = 0
            for i in site_object:
                var_obj = {}  # var_obj json dictionary is used so that the variable selected by the user can be retrieved as a session object
                count = count + 1

                variable_name = i['variable']['variableName']
                variable_id = i['variable']['variableCode']['@variableID']
                variable_text = i['variable']['variableCode']['#text']
                var_obj["variableName"] = variable_name
                var_obj["variableID"] = variable_id
                # value_type = i['variable']['valueType']
                value_count = i['valueCount']
                # data_type = i['variable']['dataType']
                # unit_name = i['variable']['unit']['unitName']
                # unit_type = i['variable']['unit']['unitType']
                # unit_abbr = i['variable']['unit']['unitAbbreviation']
                # unit_code = i['variable']['unit']['unitCode']
                # time_support = i['variable']['timeScale']['timeSupport']
                # time_support_name = i['variable']['timeScale']['unit']['unitName']
                # time_support_type = i['variable']['timeScale']['unit']['unitAbbreviation']
                begin_time = i["variableTimeInterval"]["beginDateTimeUTC"]
                begin_time = begin_time.split("T")
                begin_time = str(begin_time[0])
                end_time = i["variableTimeInterval"]["endDateTimeUTC"]
                end_time = end_time.split("T")
                end_time = str(end_time[0])
                var_obj["startDate"] = begin_time
                var_obj["endDate"] = end_time
                # print begin_time,end_time
                method_id = i["method"]["@methodID"]
                # method_desc = i["method"]["methodDescription"]
                # source_id = i["source"]["@sourceID"]
                # source_org = i["source"]["organization"]
                # source_desc = i["source"]["sourceDescription"]
                # qc_code = i["qualityControlLevel"]["qualityControlLevelCode"]
                # qc_id = i["qualityControlLevel"]["@qualityControlLevelID"]
                # qc_definition = i["qualityControlLevel"]["definition"]
                # print variable_name,variable_id, source_id,method_id, qc_code
                # Generating the string that the user sees
                variable_string = str(
                    count) + '. Variable Name:' + variable_name + ',' + 'Count: ' + value_count + ',Variable ID:' + variable_id + ', Start Date:' + begin_time + ', End Date:' + end_time
                # value_string = variable_id,variable_text,source_id,method_id,qc_code, variable_name
                value_list = [variable_text, method_id]
                value_string = str(value_list)
                # Creating a list of lists. The graph variables list will be
                # used for generating a select variable dropdown.
                graph_variables.append([variable_string, value_string])
                # Adding all the important variable metadata to a json object,
                # so that it can be retrieved later through request.session
                var_json.append(var_obj)

        else:
            # If there is a single variable do the following. The struture is
            # slightly different if there is only one variable in the site.
            # Thus this method is implemented
            var_obj = {}
            variable_name = site_object['variable']['variableName']
            variable_id = site_object['variable'][
                'variableCode']['@variableID']
            variable_text = site_object['variable']['variableCode']['#text']
            value_count = site_object['valueCount']

            # value_type = site_object['variable']['valueType']
            # data_type = site_object['variable']['dataType']
            # unit_name = site_object['variable']['unit']['unitName']
            # unit_type = site_object['variable']['unit']['unitType']
            # unit_abbr = site_object['variable']['unit']['unitAbbreviation']
            # unit_code = site_object['variable']['unit']['unitCode']
            # time_support = site_object['variable']['timeScale']['timeSupport']
            # time_support_name = site_object['variable']['timeScale']['unit']['unitName']
            # time_support_type = site_object['variable']['timeScale']['unit']['unitAbbreviation']
            begin_time = site_object[
                "variableTimeInterval"]["beginDateTimeUTC"]
            begin_time = begin_time.split("T")
            begin_time = str(begin_time[0])
            end_time = site_object["variableTimeInterval"]["endDateTimeUTC"]
            end_time = end_time.split("T")
            end_time = str(end_time[0])
            method_id = site_object["method"]["@methodID"]
            # method_desc = site_object["method"]["methodDescription"]
            # source_id = site_object["source"]["@sourceID"]
            # source_org = site_object["source"]["organization"]
            # source_desc = site_object["source"]["sourceDescription"]
            # qc_code = site_object["qualityControlLevel"]["qualityControlLevelCode"]
            # qc_id = site_object["qualityControlLevel"]["@qualityControlLevelID"]
            # qc_definition = site_object["qualityControlLevel"]["definition"]
            variable_string = '1. Variable Name:' + variable_name + ',' + 'Count: ' + value_count + \
                ',Variable ID:' + variable_id + ', Start Date:' + \
                begin_time + ', End Date:' + end_time
            # print variable_name, variable_id, source_id, method_id, qc_code
            value_list = [variable_text, method_id]
            value_string = str(value_list)
            var_obj["variableName"] = variable_name
            var_obj["variableID"] = variable_id
            var_obj["startDate"] = begin_time
            var_obj["endDate"] = end_time
            # Adding the variable metadata to a json object so that it can
            # retrieved using request.session
            var_json.append(var_obj)
            # Appending the solo variable to the empty list. This will be used
            # to generate the dropdown.
            graph_variables.append([variable_string, value_string])

        # print site_values
        # values = client.service.GetSiteInfo(site_desc)
        # print values
        select_soap_variable = SelectInput(display_text='Select Variable', name="select_var", multiple=False,
                                           options=graph_variables)  # Dropdown object for selecting a soap variable

        t_now = datetime.now()
        now_str = "{0}-{1}-{2}".format(t_now.year,
                                       check_digit(t_now.month), check_digit(t_now.day))
        start_date = DatePicker(name='start_date',
                                display_text='Start Date',
                                autoclose=True,
                                format='yyyy-mm-dd',
                                start_view='month',
                                today_button=True,
                                initial=now_str)  # Datepicker object for selecting the start date. This simply initializes the datepicker. The actual validation is done directly through JavaScript.
        end_date = DatePicker(name='end_date',
                              display_text='End Date',
                              autoclose=True,
                              format='yyyy-mm-dd',
                              start_view='month',
                              today_button=True,
                              initial=now_str)  # Datepicker object for selecting the end date. Same as above.

        select_variable = []
        graphs_object = {}
        json.JSONEncoder.default = lambda self, obj: (obj.isoformat() if isinstance(
            obj, datetime) else None)  # Encoding everything so that it can be retrieved as session object
        soap_obj["var_list"] = var_json
        # Saving the var_json as a session obj
        request.session['soap_obj'] = soap_obj

    context = {"site_name": site_name,
               "site_code": site_code,
               "network": network,
               "hs_url": hs_url,
               "service": service,
               "rest": rest,
               "soap": soap,
               "hidenav": hidenav,
               "select_soap_variable": select_soap_variable,
               "select_variable": select_variable,
               "start_date": start_date,
               "end_date": end_date,
               "graphs_object": graphs_object,
               "soap_obj": soap_obj,
               "error_message": error_message}

    return render(request, 'hydroexplorer/details.html', context)

# Controller for retrieving the REST api data


def rest_api(request):
    graphs_object = None
    if 'graphs_object' in request.session:
        graphs_object = request.session['graphs_object']
    return JsonResponse(graphs_object)

# Controller for retrieving the user selected variable for the SOAP site
# details


def soap_var(request):
    var_object = None
    if 'soap_obj' in request.session:
        var_object = request.session['soap_obj']
    return JsonResponse(var_object)


def soap_api(request):
    '''
    Controller for generating the plot for the SOAP site for a selected variable and data range
    '''
    soap_object = None
    if 'soap_obj' in request.session:
        # Requesting the session object to retrieve metadata about the site
        soap_object = request.session['soap_obj']

        url = soap_object['url']
        site_desc = soap_object['site']
        network = soap_object['network']
        variable = request.POST['select_var']
        start_date = request.POST["start_date"]
        end_date = request.POST["end_date"]
        # Manipulating the variable string to get the relevant string
        variable = str(variable)
        variable = variable.replace("[", "").replace("]", "").replace(
            "u", "").replace(" ", "").replace("'", "")
        variable = variable.split(',')
        variable_text = variable[0]
        variable_method = variable[1]
        variable_desc = network + ':' + variable_text
        client = Client(url)  # Connect to the HydroServer endpoint
        # Get values for the given site,variable, start date, end date.
        values = client.service.GetValues(
            site_desc, variable_desc, start_date, end_date, "")
        values_dict = xmltodict.parse(values)  # Converting xml to dict
        # Converting the dict to json to make it easy to parse the data
        values_json_object = json.dumps(values_dict)
        values_json = json.loads(values_json_object)
        times_series = values_json['timeSeriesResponse'][
            'timeSeries']  # Timeseries object for the variable

        # Parsing the timeseries if its not null
        if times_series['values'] is not None:
            graph_json = {}  # json object that will be returned to the front end
            graph_json["variable"] = times_series['variable']['variableName']
            graph_json["unit"] = times_series[
                'variable']['unit']['unitAbbreviation']
            graph_json["title"] = site_desc + ':' + \
                times_series['variable']['variableName']
            for j in times_series['values']:  # Parsing the timeseries
                # empty list which will have the time stamp and values within
                # the specified date range.
                data_values = []
                if j == "value":
                    # If there are multiple timeseries than value the following
                    # code is executed
                    if type((times_series['values']['value'])) is list:
                        count = 0
                        for k in times_series['values']['value']:
                            try:
                                if k['@methodCode'] == variable_method:
                                    count = count + 1
                                    time = k['@dateTimeUTC']
                                    time1 = time.replace("T", "-")
                                    time_split = time1.split("-")
                                    year = int(time_split[0])
                                    month = int(time_split[1])
                                    day = int(time_split[2])
                                    hour_minute = time_split[3].split(":")
                                    hour = int(hour_minute[0])
                                    minute = int(hour_minute[1])
                                    value = float(str(k['#text']))
                                    date_string = datetime(
                                        year, month, day, hour, minute)
                                    # Creating a timestamp as javascript cannot
                                    # recognize datetime object
                                    time_stamp = calendar.timegm(
                                        date_string.utctimetuple()) * 1000
                                    data_values.append([time_stamp, value])
                                    data_values.sort()
                                graph_json["values"] = data_values
                                graph_json["count"] = count
                            except KeyError:  # The Key Error kicks in when there is only one timeseries
                                count = count + 1
                                time = k['@dateTimeUTC']
                                time1 = time.replace("T", "-")
                                time_split = time1.split("-")
                                year = int(time_split[0])
                                month = int(time_split[1])
                                day = int(time_split[2])
                                hour_minute = time_split[3].split(":")
                                hour = int(hour_minute[0])
                                minute = int(hour_minute[1])
                                value = float(str(k['#text']))
                                date_string = datetime(
                                    year, month, day, hour, minute)
                                time_stamp = calendar.timegm(
                                    date_string.utctimetuple()) * 1000
                                data_values.append([time_stamp, value])
                                data_values.sort()
                            graph_json["values"] = data_values
                            graph_json["count"] = count
                    else:  # The else statement is executed is there is only one value in the timeseries
                        try:
                            if times_series['values']['value']['@methodCode'] == variable_method:
                                time = times_series['values'][
                                    'value']['@dateTimeUTC']
                                time1 = time.replace("T", "-")
                                time_split = time1.split("-")
                                year = int(time_split[0])
                                month = int(time_split[1])
                                day = int(time_split[2])
                                hour_minute = time_split[3].split(":")
                                hour = int(hour_minute[0])
                                minute = int(hour_minute[1])
                                value = float(
                                    str(times_series['values']['value']['#text']))
                                date_string = datetime(
                                    year, month, day, hour, minute)
                                time_stamp = calendar.timegm(
                                    date_string.utctimetuple()) * 1000
                                data_values.append([time_stamp, value])
                                data_values.sort()
                                graph_json["values"] = data_values
                                graph_json["count"] = 1
                        except KeyError:
                            time = times_series['values'][
                                'value']['@dateTimeUTC']
                            time1 = time.replace("T", "-")
                            time_split = time1.split("-")
                            year = int(time_split[0])
                            month = int(time_split[1])
                            day = int(time_split[2])
                            hour_minute = time_split[3].split(":")
                            hour = int(hour_minute[0])
                            minute = int(hour_minute[1])
                            value = float(
                                str(times_series['values']['value']['#text']))
                            date_string = datetime(
                                year, month, day, hour, minute)
                            time_stamp = calendar.timegm(
                                date_string.utctimetuple()) * 1000
                            data_values.append([time_stamp, value])
                            data_values.sort()
                            graph_json["values"] = data_values
                            graph_json["count"] = 1

    # Returning the timeseries object along with the relevant metadata
    request.session['graph_obj'] = graph_json

    return JsonResponse(graph_json)


def upload_shp(request):

    return_obj = {
        'success': False
    }

    # Converting the uploaded files into geojson object
    if request.is_ajax() and request.method == 'POST':

        file_list = request.FILES.getlist('files')
        # Convert the shapefile to geojson object. See utilities.py
        shp_json = convert_shp(file_list)
        gjson_obj = json.loads(shp_json)
        geometry = gjson_obj["features"][0]["geometry"]
        # Getting the bounds from the geometry using shapely
        shape_obj = shapely.geometry.asShape(geometry)
        poly_bounds = shape_obj.bounds
        return_obj["geometry"] = geometry
        return_obj["bounds"] = poly_bounds
        return_obj["geo_json"] = gjson_obj
        return_obj["success"] = True

        # The return object has the bounds, geometry and the geojson string.
    return JsonResponse(return_obj)
