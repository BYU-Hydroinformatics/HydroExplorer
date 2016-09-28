from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from tethys_sdk.services import get_spatial_dataset_engine, list_spatial_dataset_engines
from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from utilities import parseSites, genShapeFile, parseJSON
from json import dumps, loads
import urllib2
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import XML, fromstring, tostring
import xmltodict, json
from datetime import datetime, timedelta
from tethys_sdk.gizmos import TimeSeries, SelectInput
import time, calendar
from suds.client import Client
from django.core import serializers
import logging

geo_url_base = getattr(settings, "GEOSERVER_URL_BASE", "http://127.0.0.1:8181")
geo_user = getattr(settings, "GEOSERVER_USER_NAME", "admin")
geo_pw = getattr(settings, "GEOSERVER_USER_PASSWORD", "geoserver")

@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    context = {}

    return render(request, 'servir/home.html', context)

def add_server(request):
    return_obj = {}
    geo_url = geo_url_base +"/geoserver/rest/"

    if request.is_ajax() and request.method == 'POST':
        url = request.POST['hs-url']
        title = request.POST['hs-title']
        if url.endswith('/'):
            url = url[:-1]

        #cuahsi_validation_str = "cuahsi_1_1.asmx"
        #if cuahsi_validation_str in url:
        get_sites = url + "/GetSitesObject"
        sites_object = parseSites(get_sites)
        shapefile_object = genShapeFile(sites_object,title,geo_url,geo_user,geo_pw,url)

        geoserver_rest_url = geo_url_base+"/geoserver/wms"
        return_obj['rest_url'] = geoserver_rest_url
        return_obj['wms'] = shapefile_object["layer"]
        return_obj['bounds'] = shapefile_object["extents"]
        return_obj['title'] = title
        return_obj['url'] = url
        return_obj['status'] = "true"
    else:
        return_obj['message'] = 'This request can only be made through a "POST" AJAX call.'

    return JsonResponse(return_obj)

def details(request):

    site_name = request.GET['sitename']
    site_code = request.GET['sitecode']
    network = request.GET['network']
    hs_url = request.GET['hsurl']
    hidenav = request.GET['hidenav']
    service = request.GET['service']




    if service == 'REST':
        if hs_url.endswith(''):
            hs_url = hs_url + "/"
        site_object = network+":"+site_code

        get_site_info_url = hs_url + "GetSiteInfoObject?site="+site_object
        site_info_response = urllib2.urlopen(get_site_info_url)
        site_info_data = site_info_response.read()
        site_info_dict = xmltodict.parse(site_info_data)
        site_info_json_object = json.dumps(site_info_dict)
        site_info_json = json.loads(site_info_json_object)

        start_date = "00-00-00"
            # variable_series[0]['variableTimeInterval']['beginDateTime'][:-9]

        end_date = "3000-01-01"
            # variable_series[0]['variableTimeInterval']['endDateTime'][:-9]


        site_values_url = hs_url +"GetValuesForASiteObject?site="+site_object+"&startDate="+start_date+"&endDate="+end_date

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
                    graph_json["unit"] = i['variable']['unit']['unitAbbreviation']
                    graph_json["title"] = site_name+':'+i['variable']['variableName']
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
                                    date_string = datetime(year,month,day,hour,minute)
                                    time_stamp = calendar.timegm(date_string.utctimetuple())
                                    data_values.append([time_stamp,value])
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
                                value = float(str(i['values']['value']['#text']))
                                date_string = datetime(year, month, day, hour, minute)
                                time_stamp = calendar.timegm(date_string.utctimetuple())
                                data_values.append([time_stamp, value])
                                data_values.sort()
                                graph_json["values"] = data_values
                    graphs.append(graph_json)
        else:
            if times_series['values'] is not None:
                graph_json = {}
                graph_json["variable"] = times_series['variable']['variableName']
                graph_json["unit"] = times_series['variable']['unit']['unitAbbreviation']
                graph_json["title"] = site_name + ':' + times_series['variable']['variableName']
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
                                date_string = datetime(year, month, day, hour, minute)
                                time_stamp = calendar.timegm(date_string.utctimetuple())
                                data_values.append([time_stamp, value])
                                data_values.sort()
                            graph_json["values"] = data_values
                        else:
                            time = times_series['values']['value']['@dateTimeUTC']
                            time1 = time.replace("T", "-")
                            time_split = time1.split("-")
                            year = int(time_split[0])
                            month = int(time_split[1])
                            day = int(time_split[2])
                            hour_minute = time_split[3].split(":")
                            hour = int(hour_minute[0])
                            minute = int(hour_minute[1])
                            value = float(str(times_series['values']['value']['#text']))
                            date_string = datetime(year, month, day, hour, minute)
                            time_stamp = calendar.timegm(date_string.utctimetuple())
                            data_values.append([time_stamp, value])
                            data_values.sort()
                            graph_json["values"] = data_values
                graphs.append(graph_json)
            else:
                print "No data"

        graphs_object = {}
        graphs_object["graph"] = graphs
        # print graphs_object
        graph_variables = []
        for var in graphs_object["graph"]:
            graph_variables.append([var["variable"],var["variable"]])

        # graph_title = site_name + ":" + graphs_object['graph'][-1]['variable']
        # graph_axis_title = graphs_object['graph'][-1]['variable']
        # graph_unit = graphs_object['graph'][-1]['unit']
        #
        # timeseries_plot = TimeSeries(
        #     height='250px',
        #     width='500px',
        #     engine='highcharts',
        #     title=graph_title,
        #     y_axis_title= graph_axis_title,
        #     y_axis_units=graph_unit,
        #     series=[{
        #         'name': graph_axis_title,
        #         'data': graphs_object['graph'][-1]['values']
        #     }]
        # )

        select_variable = SelectInput(display_text='Select variable',name="select_var",multiple=False,options=graph_variables)

            # print i['variable']


        # for i in series:
        #     print i['variable']['variableName']
        #     print i['variableTimeInterval']['beginDateTime'][:-9]
        #     print i['variableTimeInterval']['endDateTime'][:-9]

        # print graphs_object
        json.JSONEncoder.default = lambda self, obj: (obj.isoformat() if isinstance(obj, datetime) else None)
        request.session['graphs_object'] = graphs_object
    if service == 'SOAP':
        client = Client(hs_url)
        client.set_options(port='WaterOneFlow')
        site_desc = site_code+":"+network
        site_info = client.service.GetSiteInfo(site_desc)
        site_info = site_info.encode('utf-8')
        site_values = client.service.GetValuesForASiteObject(site_desc,"","","")
        print site_info
        print site_values

        # print site_values
        # values = client.service.GetSiteInfo(site_desc)
        # print values
        select_variable = SelectInput(display_text='Select variable', name="select_var", multiple=False,
                                      options=["life","life"])
        graphs_object = {}

    context = {"site_name":site_name,"site_code":site_code,"network":network,"hs_url":hs_url,"hidenav":hidenav,"select_variable":select_variable,"graphs_object":graphs_object}



    return render(request, 'servir/details.html', context)

def api(request):
    graphs_object = None
    if 'graphs_object' in request.session:
        graphs_object = request.session['graphs_object']
    return JsonResponse(graphs_object)

def soap(request):
    return_obj = {}
    if request.is_ajax() and request.method == 'POST':

        logging.getLogger('suds.client').setLevel(logging.CRITICAL)
        # soap_url = 'http://worldwater.byu.edu/app/index.php/sediment/services/cuahsi_1_1.asmx?WSDL'
        geo_url = geo_url_base + "/geoserver/rest/"
        # soap_url = 'http://hydroportal.cuahsi.org/GlobalRiversObservatory/webapp/cuahsi_1_1.asmx?WSDL'
        url = request.POST['soap-url']
        title = request.POST['soap-title']
        client = Client(url)
        client.set_options(port='WaterOneFlow')
        sites = client.service.GetSites('[:]')
        # sites = client.service.GetSites()
        # print sites
        sites_dict = xmltodict.parse(sites)
        sites_json_object = json.dumps(sites_dict)
        sites_json = json.loads(sites_json_object)
        sites_object = parseJSON(sites_json)
        shapefile_object = genShapeFile(sites_object,title,geo_url,geo_user,geo_pw,url)

        geoserver_rest_url = geo_url_base + "/geoserver/wms"
        return_obj['rest_url'] = geoserver_rest_url
        return_obj['wms'] = shapefile_object["layer"]
        return_obj['bounds'] = shapefile_object["extents"]
        return_obj['title'] = title
        return_obj['url'] = url
        return_obj['status'] = "true"
    else:
        return_obj['message'] = 'This request can only be made through a "POST" AJAX call.'


    return  JsonResponse(return_obj)