import xml.etree.ElementTree as et
import urllib2
import shapefile as sf
import os, tempfile, shutil, sys, zipfile, string, random
from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine
from tethys_sdk.services import get_spatial_dataset_engine
import requests
from owslib.waterml.wml11 import WaterML_1_1 as wml11
from suds.client import Client
from suds.sudsobject import asdict
from suds.sudsobject import asdict
import json


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
def parseWML(bbox):
    hs_sites = []
    # print bbox
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

    bbox_json = recursive_asdict(bbox)

    if type(bbox_json['site']) is list:
        for site in bbox_json['site']:
            hs_json = {}
            site_name =  site['siteInfo']['siteName']
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

def check_digit(num):
    num_str = str(num)
    if len(num_str) < 2:
        num_str = '0' + num_str
    return num_str