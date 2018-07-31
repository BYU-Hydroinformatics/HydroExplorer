# HydroExplorer - Water Observations Data Integerator

This app is created to run in the [Tethys Platform Environment](https://github.com/tethysplatform/tethys) [(Documentation)](http://docs.tethysplatform.org/en/latest/)

## Prerequisites:

* Tethys Platform (CKAN, PostgresQL, GeoServer)
* pyshp (Python package for uploading shapefiles to geoserver)
* pyproj (Python package for projecting coordinates)
* suds (lightweight SOAP python client for consuming Web Services.)

## Install Tathys Platform

See: http://docs.tethysplatform.org/en/latest/installation.html

## Install Dependencies

### Automatic

The below dependencies will be installed when you run the following command

```bash
python setup.py develop
```

However, if the installation fails, you may be able to install the dependencies individually by following the steps below:

### Manual Dependency Installation:

#### Install pyshp into Tethys' Python environment:

```
$ sudo su
$ . /usr/lib/tethys/bin/activate
$ pip install pyshp
$ exit
```

#### Install pyproj into Tethys' Python environment:

```
$ sudo su
$ . /usr/lib/tethys/bin/activate
$ pip install pyproj
$ exit
```

####Install suds into Tethys' Python environment:

```
$ sudo su
$ . /usr/lib/tethys/bin/activate
$ pip install suds
$ exit
```

## Application Installation:

Clone and install

```bash
git clone https://github.com/BYU-Hydroinformatics/HydroExplorer.git
cd HydroExplorer
python setup.py install/develop
tethys manage collectstatic (Only required for production installation)
```

### Enable CORS on geoserver (To enable tiles to show up from the geoserver)

#### For Tethys 1.3

Create a new bash session in the tethys_geoserver docker container:

```
$ . /usr/lib/tethys/bin/activate
$ docker exec -it tethys_geoserver /bin/bash
$ vi /var/lib/tomcat7/webapps/geoserver/WEB-INF/web.xml
```

Insert the following in the filters list:

```
<filter>
    <filter-name>CorsFilter</filter-name>
    <filter-class>org.apache.catalina.filters.CorsFilter</filter-class>
    <init-param>
      <param-name>cors.allowed.origins</param-name>
      <param-value>http://127.0.0.1:8000, http://127.0.0.1:8181</param-value>
    </init-param>
</filter>
```

Insert this filter-mapping to the filter-mapping list:

```
<filter-mapping>
    <filter-name>CorsFilter</filter-name>
    <url-pattern>/*</url-pattern>
</filter-mapping>
```

Save the web.xml file.

```
$ exit
$ docker restart tethys_geoserver
```

#### For Tethys 1.4

Create a new bash session in the tethys_geoserver docker container:

```
$ . /usr/lib/tethys/bin/activate
$ docker exec -it tethys_geoserver /bin/bash
$ cd node1/webapps/geoserver/WEB-INF
$ vi web.xml
```

Note: You can make this change to any other node in the geoserver docker.

Insert the following in the filters list:

```
<filter>
    <filter-name>CorsFilter</filter-name>
    <filter-class>org.apache.catalina.filters.CorsFilter</filter-class>
    <init-param>
      <param-name>cors.allowed.origins</param-name>
      <param-value>http://127.0.0.1:8000, http://127.0.0.1:8181</param-value>
    </init-param>
</filter>
```

Insert this filter-mapping to the filter-mapping list:

```
<filter-mapping>
    <filter-name>CorsFilter</filter-name>
    <url-pattern>/*</url-pattern>
</filter-mapping>
```

Save the web.xml file.

```
$ exit
$ docker restart tethys_geoserver
```

## Future Planned Changes

* Add ability to refresh list of sites within a hydroserver entry. Or maybe auto refresh?
* Delete Hydroservers should be a multi select
* Add HydroServers from Catalog should be a multi/all add select

## Changelog

## [Unreleased]

### Added

* Modularized the home template by breaking all the Modals apart
* Ability to add/delete a CUAHSI Compatible Catalog Service
* Save Sites information to the database instead of a WMS Layer
* Notification system instead of updating status div within modals

### Changed

* Map cleaned up and expanded to fill up the whole screen
* Moved List of Hydroservers to top actions bar
* Fix CSV Download on HighCharts
* ReadMe
* Fetch list of hydroservers from catalog dynamically
* Creation of dynamic popovers when clicking features instead of getting info from WMS service

### Removed

* Dependencies on local HighCharts
* GeoServer connection and dependency on WMS Layers

## [1.0.0] - 2017

### Added

* Initial Commit
