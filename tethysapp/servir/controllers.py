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
import unicodedata

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
    rest = None
    soap = None


    if service == 'REST':
        if hs_url.endswith(''):
            hs_url = hs_url + "/"
        site_object = network+":"+site_code
        rest = service
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
        select_soap_variable = []
            # print i['variable']


        # for i in series:
        #     print i['variable']['variableName']
        #     print i['variableTimeInterval']['beginDateTime'][:-9]
        #     print i['variableTimeInterval']['endDateTime'][:-9]

        # print graphs_object
        json.JSONEncoder.default = lambda self, obj: (obj.isoformat() if isinstance(obj, datetime) else None)
        request.session['graphs_object'] = graphs_object
        soap_obj = {}
    if service == 'SOAP':
        soap_obj = {}
        soap = service
        soap_obj["url"] = hs_url

        client = Client(hs_url)
        client.set_options(port='WaterOneFlow')
        site_desc = network+":"+site_code
        soap_obj["site"] = site_desc
        soap_obj["network"] = network
        site_info = client.service.GetSiteInfo(site_desc)
        site_info = site_info.encode('utf-8')
        # site_values = client.service.GetValuesForASiteObject(site_desc,"","","")
        # print site_values
        info_dict = xmltodict.parse(site_info)
        info_json_object = json.dumps(info_dict)
        info_json = json.loads(info_json_object)
        # print site_values
        # print info_json
        site_variables = []
        site_object = info_json['sitesResponse']['site']['seriesCatalog']['series']
        graph_variables = []

        if type(site_object) is list:
            count = 0
            for i in site_object:
                count = count + 1
                variable_name =  i['variable']['variableName']
                variable_id = i['variable']['variableCode']['@variableID']
                variable_text = i['variable']['variableCode']['#text']
                value_type = i['variable']['valueType']
                value_count = i['valueCount']
                data_type = i['variable']['dataType']
                unit_name = i['variable']['unit']['unitName']
                unit_type = i['variable']['unit']['unitType']
                unit_abbr = i['variable']['unit']['unitAbbreviation']
                unit_code = i['variable']['unit']['unitCode']
                time_support = i['variable']['timeScale']['timeSupport']
                time_support_name = i['variable']['timeScale']['unit']['unitName']
                time_support_type = i['variable']['timeScale']['unit']['unitAbbreviation']
                begin_time = i["variableTimeInterval"]["beginDateTimeUTC"]
                end_time = i["variableTimeInterval"]["endDateTimeUTC"]
                print begin_time,end_time
                method_id = i["method"]["@methodID"]
                method_desc = i["method"]["methodDescription"]
                source_id = i["source"]["@sourceID"]
                source_org = i["source"]["organization"]
                source_desc = i["source"]["sourceDescription"]
                qc_code = i["qualityControlLevel"]["qualityControlLevelCode"]
                qc_id = i["qualityControlLevel"]["@qualityControlLevelID"]
                qc_definition = i["qualityControlLevel"]["definition"]
                # print variable_name,variable_id, source_id,method_id, qc_code
                variable_string = str(count)+'. Variable Name:'+variable_name+','+'Count: '+value_count+',Variable ID:'+variable_id+','+'Source ID:'+source_id+','+'Method ID:'+method_id+','+'Quality Control Code:'+qc_code
                # value_string = variable_id,variable_text,source_id,method_id,qc_code, variable_name
                value_list = [variable_text, method_id]
                value_string = str(value_list)
                graph_variables.append([variable_string,value_string])
                # print variable_name, variable_id, value_type, data_type, unit_name,unit_type, unit_abbr,unit_abbr,unit_code, time_support, time_support_name, time_support_type
        else:
            variable_name = site_object['variable']['variableName']
            variable_id = site_object['variable']['variableCode']['@variableID']
            variable_text = site_object['variable']['variableCode']['#text']
            value_count = site_object['valueCount']
            value_type = site_object['variable']['valueType']
            data_type = site_object['variable']['dataType']
            unit_name = site_object['variable']['unit']['unitName']
            unit_type = site_object['variable']['unit']['unitType']
            unit_abbr = site_object['variable']['unit']['unitAbbreviation']
            unit_code = site_object['variable']['unit']['unitCode']
            time_support = site_object['variable']['timeScale']['timeSupport']
            time_support_name = site_object['variable']['timeScale']['unit']['unitName']
            time_support_type = site_object['variable']['timeScale']['unit']['unitAbbreviation']
            begin_time = site_object["variableTimeInterval"]["beginDateTimeUTC"]
            end_time = site_object["variableTimeInterval"]["endDateTimeUTC"]
            method_id = site_object["method"]["@methodID"]
            method_desc = site_object["method"]["methodDescription"]
            source_id = site_object["source"]["@sourceID"]
            source_org = site_object["source"]["organization"]
            source_desc = site_object["source"]["sourceDescription"]
            qc_code = site_object["qualityControlLevel"]["qualityControlLevelCode"]
            qc_id = site_object["qualityControlLevel"]["@qualityControlLevelID"]
            qc_definition = site_object["qualityControlLevel"]["definition"]
            variable_string = '1. Variable Name:' + variable_name + ',' + 'Count: '+value_count+',Variable ID:' + variable_id + ',' + 'Source ID:' + source_id + ',' + 'Method ID:' + method_id + ',' + 'Quality Control Code:' + qc_code
            # print variable_name, variable_id, source_id, method_id, qc_code
            value_list = [variable_text,method_id]
            value_string = str(value_list)
            graph_variables.append([variable_string, value_string])




        # print site_values
        # values = client.service.GetSiteInfo(site_desc)
        # print values
        select_soap_variable = SelectInput(display_text='Select Variable', name="select_var", multiple=False,
                                      options=graph_variables)
        select_variable = []
        graphs_object = {}
        json.JSONEncoder.default = lambda self, obj: (obj.isoformat() if isinstance(obj, datetime) else None)
        request.session['soap_obj'] = soap_obj

    context = {"site_name":site_name,"site_code":site_code,"network":network,"hs_url":hs_url,"service":service,"rest":rest,"soap":soap,"hidenav":hidenav,"select_soap_variable":select_soap_variable,"select_variable":select_variable,"graphs_object":graphs_object,"soap_obj":soap_obj}



    return render(request, 'servir/details.html', context)

def rest_api(request):
    graphs_object = None
    if 'graphs_object' in request.session:
        graphs_object = request.session['graphs_object']
    return JsonResponse(graphs_object)

def soap_api(request):
    soap_object = None
    values_json = {}
    if 'soap_obj' in request.session:
            soap_object = request.session['soap_obj']
            url = soap_object['url']
            site_desc = soap_object['site']
            network = soap_object['network']
            variable =  request.POST['select_var']
            variable =  str(variable)
            variable =  variable.replace("[","").replace("]","").replace("u","").replace(" ","").replace("'","")
            variable = variable.split(',')
            variable_text = variable[0]
            variable_method = variable[1]
            variable_desc = network+':'+variable_text

            client = Client(url)
            values = client.service.GetValues(site_desc,variable_desc,"","","")
            values_dict = xmltodict.parse(values)
            values_json_object = json.dumps(values_dict)
            values_json = json.loads(values_json_object)
            times_series = values_json['timeSeriesResponse']['timeSeries']
            if times_series['values'] is not None:
                graph_json = {}
                graph_json["variable"] = times_series['variable']['variableName']
                graph_json["unit"] = times_series['variable']['unit']['unitAbbreviation']
                graph_json["title"] = site_desc + ':' + times_series['variable']['variableName']
                for j in times_series['values']:
                    data_values = []
                    if j == "value":
                        if type((times_series['values']['value'])) is list:
                            count = 0
                            for k in times_series['values']['value']:
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
                                    date_string = datetime(year, month, day, hour, minute)
                                    time_stamp = calendar.timegm(date_string.utctimetuple())
                                    data_values.append([time_stamp, value])
                                    data_values.sort()
                                graph_json["values"] = data_values
                                graph_json["count"] = count
                        else:
                            if times_series['values']['value']['@methodCode'] == variable_method:
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
                                graph_json["count"] = 1

    return JsonResponse(graph_json)

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