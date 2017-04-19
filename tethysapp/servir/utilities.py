import xml.etree.ElementTree as ET
import urllib2
import shapefile as sf
import os, tempfile, shutil, sys, zipfile, string, random
from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine
from tethys_sdk.services import get_spatial_dataset_engine
import requests
from owslib.waterml.wml11 import WaterML_1_1 as wml11
from suds.client import Client
from suds.sudsobject import asdict
import json
from owslib.waterml.wml11 import WaterML_1_1 as wml11
from dateutil import parser as dateparser
from datetime import datetime
import inspect
import xmltodict
import dateutil.relativedelta
from datetime import date, timedelta
from datetime import *
from json import dumps
import time, calendar
import functools
import fiona
import geojson
import pyproj
import shapely.geometry
import shapely.ops
import os, tempfile, shutil, sys

try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

extract_base_path = '/tmp'
def parseSites(xml):
    response = urllib2.urlopen(xml)
    data = response.read()

    parse_xml = et.fromstring(data)
    hs_sites = []
    for child in parse_xml:
        for items in child:
            get_contents = items.tag
            # Narrowing down to the DataInputs tag
            if get_contents.find('siteInfo') != -1:
                for location in items:
                    descriptor = location.tag
                    if descriptor.find('siteName') != -1:
                        site_name = location.text
                        hs_json = {}
                        hs_json["sitename"] = site_name
                        hs_json["service"] = "REST"
                        #print "Site Name: "+site_name
                    if descriptor.find('siteCode') != -1:
                        site_code = location.text
                        #print "Site Code: "+site_code
                        source = location.get('network')
                        hs_json['network'] = source
                        hs_json["sitecode"] = site_code
                    if descriptor.find('elevation') != -1:
                        elevation = location.text
                        #print "Elevation: " + elevation
                        hs_json["elevation"] = elevation
                    for geoLocation in location:
                        for coords in geoLocation:
                            latlon = coords.tag
                            if latlon.find('latitude') != -1:
                                latitude = coords.text
                                #print "Latitude: " + latitude
                                hs_json["latitude"] = latitude
                            if latlon.find('longitude')!= -1:
                                longitude = coords.text
                                #print "Longitude: " + longitude
                                hs_json["longitude"] = longitude
                hs_sites.append(hs_json)

    return hs_sites
def parseOWS(wml):
    hs_sites = []
    for site in wml.sites:
        hs_json = {}
        site_name =  site.name
        site_name = site_name.encode("utf-8")
        site_code =  site.codes[0]
        latitude = site.latitudes
        longitude =  site.longitudes
        network =  site.site_info.elevation

        hs_json["sitename"] = site_name

        hs_json["latitude"] = latitude
        hs_json["longitude"] = longitude
        hs_json["sitecode"] = site_code
        hs_json["network"] = network
        hs_json["service"] = "SOAP"
        hs_sites.append(hs_json)

    return hs_sites


def recursive_asdict(d):
    """Convert Suds object into serializable format."""
    out = {}
    for k, v in asdict(d).iteritems():
        if hasattr(v, "__keylist__"):
            out[k] = recursive_asdict(v)
        elif isinstance(v, list):
            out[k] = []
            for item in v:
                if hasattr(item, "__keylist__"):
                    out[k].append(recursive_asdict(item))
                else:
                    out[k].append(item)
        else:
            out[k] = v
    return out


def suds_to_json(data):
    return json.dumps(recursive_asdict(data))

def parseWML(bbox):
    hs_sites = []
    # print bbox


    bbox_json = recursive_asdict(bbox)

    if type(bbox_json['site']) is list:
        for site in bbox_json['site']:
            hs_json = {}
            site_name =  site['siteInfo']['siteName']
            site_name = site_name.encode("utf-8")
            latitude = site['siteInfo']['geoLocation']['geogLocation']['latitude']
            longitude = site['siteInfo']['geoLocation']['geogLocation']['longitude']
            network = site['siteInfo']['siteCode'][0]['_network']
            sitecode = site['siteInfo']['siteCode'][0]['value']

            hs_json["sitename"] = site_name
            hs_json["latitude"] = latitude
            hs_json["longitude"] = longitude
            hs_json["sitecode"] = sitecode
            hs_json["network"] = network
            hs_json["service"] = "SOAP"
            hs_sites.append(hs_json)
    else:
        hs_json = {}
        site_name = bbox_json['site']['siteInfo']['siteName']
        site_name = site_name.encode("utf-8")
        latitude = bbox_json['site']['siteInfo']['geoLocation']['geogLocation']['latitude']
        longitude = bbox_json['site']['siteInfo']['geoLocation']['geogLocation']['longitude']
        network = bbox_json['site']['siteInfo']['siteCode'][0]['_network']
        sitecode = bbox_json['site']['siteInfo']['siteCode'][0]['value']

        hs_json["sitename"] = site_name
        hs_json["latitude"] = latitude
        hs_json["longitude"] = longitude
        hs_json["sitecode"] = sitecode
        hs_json["network"] = network
        hs_json["service"] = "SOAP"
        hs_sites.append(hs_json)

    return hs_sites
def parseJSON(json):
    hs_sites = []
    sites_object =  json['sitesResponse']['site']
    if type(sites_object) is list:
        for site in sites_object:
            hs_json = {}
            latitude = site['siteInfo']['geoLocation']['geogLocation']['latitude']
            longitude = site['siteInfo']['geoLocation']['geogLocation']['longitude']
            site_name = site['siteInfo']['siteName']
            site_name = site_name.encode("utf-8")
            network = site['siteInfo']['siteCode']["@network"]
            sitecode = site['siteInfo']['siteCode']["#text"]

            hs_json["sitename"] = site_name
            hs_json["latitude"] = latitude
            hs_json["longitude"] = longitude
            hs_json["sitecode"] = sitecode
            hs_json["network"] = network
            hs_json["service"] = "SOAP"
            hs_sites.append(hs_json)
    else:
        hs_json = {}
        latitude = sites_object['siteInfo']['geoLocation']['geogLocation']['latitude']
        longitude = sites_object['siteInfo']['geoLocation']['geogLocation']['longitude']
        site_name = sites_object['siteInfo']['siteName']
        site_name = site_name.encode("utf-8")
        network = sites_object['siteInfo']['siteCode']["@network"]
        sitecode = sites_object['siteInfo']['siteCode']["#text"]

        hs_json["sitename"] = site_name
        hs_json["latitude"] = latitude
        hs_json["longitude"] = longitude
        hs_json["sitecode"] = sitecode
        hs_json["network"] = network
        hs_json["service"] = "SOAP"
        hs_sites.append(hs_json)

    return hs_sites


def genShapeFile(input,title,geo_url,username,password,hs_url):
    try:
        file_name = 'hs_sites'
        temp_dir = tempfile.mkdtemp()
        file_location = temp_dir+"/"+file_name
        w = sf.Writer(sf.POINT)
        w.field('sitename')
        w.field('sitecode')
        w.field('network')
        w.field('service')
        w.field('url','C',200)
        # w.field('elevation')

        for item in input:
            w.point(float(item['longitude']),float(item['latitude']))
            site_name = item['sitename']
            site_name.decode("utf-8")
            w.record(item['sitename'],item['sitecode'],item['network'],item['service'],hs_url, 'Point')

        w.save(file_location)
        prj = open("%s.prj" % file_location, "w")
        epsg = 'GEOGCS["WGS84",DATUM["WGS_1984",SPHEROID["WGS84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
        prj.write(epsg)
        prj.close()

        file_list = os.listdir(temp_dir)

        zip_file_full_path = temp_dir + "/" + "shapefile.zip"

        with zipfile.ZipFile(zip_file_full_path, 'a') as myzip:
            for fn in file_list:
                shapefile_fp = temp_dir + "/"+ fn  # tif full path
                new_file_name = title + os.path.splitext(fn)[1]
                myzip.write(shapefile_fp, arcname=new_file_name)

        #Connecting to geoserver
        spatial_dataset_engine = GeoServerSpatialDatasetEngine(endpoint=geo_url, username=username, password=password)
        layer_metadata = {}

        response = None
        ws_name = "catalog"
        result = spatial_dataset_engine.create_workspace(workspace_id=ws_name, uri="www.servir.org")
        if result['success']:
            print "Created workspace " + ws_name + " successfully"
        else:
            print "Creating workspace " + ws_name + " failed"
        #print result

        store_id = ws_name + ":" + title

        result = None
        result = spatial_dataset_engine.create_shapefile_resource(store_id=store_id, shapefile_zip=zip_file_full_path)
        if result['success']:
            print "Created store " + title + " successfully"
        else:
            print "Creating store " + title + " failed"


        #find the bbox area
        wms_rest_url = '{}workspaces/{}/datastores/{}/featuretypes/{}.json'.format(geo_url,ws_name,title,title)
        print wms_rest_url
        r = requests.get(wms_rest_url, auth=(username,password))
        if r.status_code != 200:
            print 'The Geoserver appears to be down.'
        else:
            json = r.json()
            extents = json['featureType']['latLonBoundingBox']
        # wms_response = urllib2.urlopen(wms_rest_url)
        # wms_data = wms_response.read()
        # print wms_data
        layer_metadata["layer"] = store_id
        layer_metadata["extents"] = extents




        return layer_metadata

    except:
        return False
    finally:
        if temp_dir is not None:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
def parse_gldas_data(file):
    data = []
    data_flag_text = 'Date&Time'
    error_flag_text = 'ERROR:'
    error_message = None
    found_data = False
    file = file.split("\n")
    s_lines = []

    for line in file:
        if data_flag_text in line:
            found_data = True
            continue
        if found_data:
            s_lines.append(line)


    try:
        if len(s_lines) < 1:
            raise Exception
    except Exception as e:
        raise e

    for row in s_lines:
        row_ls = row.strip().replace(' ', '-', 1).split()

        try:
            if len(row_ls) == 2:
                date = row_ls[0]
                val = row_ls[1]
                date_val_pair =[datetime.strptime(date, '%Y-%m-%d-%HZ'),float(val)]
                data.append(date_val_pair)
        except Exception as e:
            print str(e),"Exception"
            continue

    return data

def gen_gldas_dropdown():
    gldas_options = []
    gldas_config_file = inspect.getfile(inspect.currentframe()).replace('utilities.py',
                                                                'public/data/gldas_config.txt')

    with open(gldas_config_file,mode='r') as f:
        f.readline()
        for line in f:
            linevals = line.split('|')
            var_name = linevals[1]
            var_units = linevals[2]
            display_str = var_name+" "+var_units
            value_str = str(line)
            gldas_options.append([display_str, value_str])



    return gldas_options

def get_loc_name(lat,lon):

    geo_coords = str(lat) + "," + str(lon)
    geo_api = "http://maps.googleapis.com/maps/api/geocode/json?latlng={0}&sensor=true".format(geo_coords)
    open_geo = urllib2.urlopen(geo_api)
    open_geo = open_geo.read()
    location_json = json.loads(open_geo,"utf-8")
    name = location_json['results'][0]['formatted_address']
    name = name.encode("utf-8")
    return name

def check_digit(num):
    num_str = str(num)
    if len(num_str) < 2:
        num_str = '0' + num_str
    return num_str

def process_job_id(url,operation_type_var):

    open_data_url = urllib2.urlopen(url)
    read_data_response = open_data_url.read()
    data_json = json.loads(read_data_response)
    graph_values = []
    for i in data_json["data"]:

        time = int(i["epochTime"])

        if operation_type_var == "max":
            value = i["value"]["max"]
        elif operation_type_var == "min":
            value = i["value"]["min"]
        elif operation_type_var == "avg":
            value = i["value"]["avg"]

        graph_values.append([datetime.fromtimestamp(time),value])


    return graph_values

def get_gldas_range():

    begin_url1 = "https://cmr.earthdata.nasa.gov/search/granules?short_name=GLDAS_NOAH025SUBP_3H&version=001&page_size=1&sort_key=start_date"
    open_begin_url1 = urllib2.urlopen(begin_url1)
    read_begin_url1 = open_begin_url1.read()
    begin_url1_data = xmltodict.parse(read_begin_url1)
    begin_url2 = begin_url1_data['results']['references']['reference']['location']

    open_begin_url2 = urllib2.urlopen(begin_url2)
    read_begin_url2 = open_begin_url2.read()
    begin_url2_data = xmltodict.parse(read_begin_url2)
    start_date = begin_url2_data['Granule']['Temporal']['RangeDateTime']['BeginningDateTime']
    start_date = start_date.split('T')[0]
    # start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
    end_url1 = "https://cmr.earthdata.nasa.gov/search/granules?short_name=GLDAS_NOAH025SUBP_3H&version=001&page_size=1&sort_key=-start_date"
    open_end_url1 = urllib2.urlopen(end_url1)
    read_end_url1 = open_end_url1.read()
    end_url1_data = xmltodict.parse(read_end_url1)
    end_url2 = end_url1_data['results']['references']['reference']['location']

    open_end_url2 = urllib2.urlopen(end_url2)
    read_end_url2 = open_end_url2.read()
    end_url2_data = xmltodict.parse(read_end_url2)
    end_date = end_url2_data['Granule']['Temporal']['RangeDateTime']['BeginningDateTime']

    end_date_str = end_date.split('T')[0]
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    first = end_date.replace(day=1)
    lastMonth = first - timedelta(days=1)
    end_date = lastMonth.strftime("%Y-%m-%d")
    range = {"start":start_date,"end":end_date}

    return range




def get_sf_range():
    try:
        scenario_url = "http://limateserv.servirglobal.net/chirps/getClimateScenarioInfo/"
        response = urllib2.urlopen(scenario_url)
        read_response = response.read()
        data_json = json.loads(read_response)
        capability = data_json["climate_DataTypeCapabilities"][0]["current_Capabilities"]
        capability = json.loads(capability)
        start_date = capability["startDateTime"]
        end_date = capability["endDateTime"]
        start_date = datetime.strptime(start_date, '%Y_%m_%d').strftime('%m/%d/%Y')
        end_date = datetime.strptime(end_date, '%Y_%m_%d').strftime('%m/%d/%Y')
        range = {"start":start_date,"end":end_date}
        return range
    except Exception as e:
        range = {"start": "00/00/0000", "end": "00/00/0000"}
        return range

def get_climate_scenario(ensemble,variable):

    scenario_url = "http://climateserv.servirglobal.net/chirps/getClimateScenarioInfo/"
    response = urllib2.urlopen(scenario_url)
    read_response =  response.read()
    data_json = json.loads(read_response)

    for i in data_json["climate_DatatypeMap"]:
        if i["climate_Ensemble"] == ensemble:
            for j in i["climate_DataTypes"]:
                if j["climate_Variable_Label"] == variable:
                    data_type_number = j["dataType_Number"]
                    return data_type_number

def convert_shp(files):
    geojson_string = ''
    try:
        temp_dir = tempfile.mkdtemp()
        for f in files:
            f_name = f.name
            f_path = os.path.join(temp_dir,f_name)

            with open(f_path,'wb') as f_local:
                f_local.write(f.read())


        for file in os.listdir(temp_dir):
            if file.endswith(".shp"):
                f_path = os.path.join(temp_dir,file)
                omit = ['SHAPE_AREA', 'SHAPE_LEN']

                with fiona.open(f_path) as source:
                    project = functools.partial(pyproj.transform,
                                                pyproj.Proj(**source.crs),
                                                pyproj.Proj(init='epsg:3857'))
                    features = []
                    for f in source:
                        shape = shapely.geometry.shape(f['geometry'])
                        projected_shape = shapely.ops.transform(project, shape)

                        # Remove the properties we don't want
                        props = f['properties']  # props is a reference
                        for k in omit:
                            if k in props:
                                del props[k]

                        feature = geojson.Feature(id=f['id'],
                                                  geometry=projected_shape,
                                                  properties=props)
                        features.append(feature)
                    fc = geojson.FeatureCollection(features)

                    geojson_string = geojson.dumps(fc)


    except:
        return 'error'
    finally:
        if temp_dir is not None:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                # for file in files:
                #     if str(file).endswith('.shp'):
                #         reader = shapefile.Reader(file)
                #         fields = reader.fields[1:]
                #         field_names = [field[0] for field in fields]
                #         buffer = []
                #         for sr in reader.shapeRecords():
                #             atr = dict(zip(field_names, sr.record))
                #             geom = sr.shape.__geo_interface__
                #             buffer.append(dict(type="Feature", geometry=geom, properties=atr))

                # print buffer

    return geojson_string
