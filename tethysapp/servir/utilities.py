import xml.etree.ElementTree as et
import urllib2
import shapefile as sf
import os, tempfile, shutil, sys, zipfile, string, random
from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine
from tethys_sdk.services import get_spatial_dataset_engine
import requests


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


def genShapeFile(input,title,geo_url,username,password,hs_url):
    try:
        file_name = 'hs_sites'
        temp_dir = tempfile.mkdtemp()
        file_location = temp_dir+"/"+file_name
        w = sf.Writer(sf.POINT)
        w.field('sitename')
        w.field('sitecode')
        w.field('network')
        w.field('url','C',200)
        # w.field('elevation')

        for item in input:
            w.point(float(item['longitude']),float(item['latitude']))
            w.record(item['sitename'],item['sitecode'],item['network'],hs_url, 'Point')

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


