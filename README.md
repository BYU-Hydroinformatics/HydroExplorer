#Servir Water Observations Data Integerator

**This app is created to run in the Teyths Platform programming environment.
See: https://github.com/tethysplatform/tethys and http://docs.tethysplatform.org/en/latest/**

##Prerequisites:
- Tethys Platform (CKAN, PostgresQL, GeoServer)
- pyshp (Python package for uploading shapefiles to geoserver)
- pyproj (Python package for projecting coordinates)
- suds (lightweight SOAP python client for consuming Web Services.)


###Install Tathys Platform
See: http://docs.tethysplatform.org/en/latest/installation.html

###Install Dependencies
The below dependencies will be installed when you run the following command

```
python setup.py develop
```

However, if the installation fails, you may be able to install the dependencies individually by following the steps below: 

###Manual Dependency Installation:

####Install pyshp into Tethys' Python environment:
```
$ sudo su
$ . /usr/lib/tethys/bin/activate
$ pip install pyshp
$ exit
```
####Install pyproj into Tethys' Python environment:
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

##Installation:
Clone the app into the directory you want:
```
$ git clone https://github.com/SarvaPulla/servirdi.git
$ cd servirdi
```

Then install the app into the Tethys Platform.

###Installation for App Development:
```
$ . /usr/lib/tethys/bin/activate
$ cd servirdi
$ python setup.py develop
```
###Installation for Production:
```
$ . /usr/lib/tethys/bin/activate
$ cd servirdi
$ python setup.py install
$ tethys manage collectstatic
```
####Ensure services are provided to the app : 

@TODO : 



```
$ . /usr/lib/tethys/bin/activate
$ sudo su
$ cd /usr/lib/tethys/src/tethys_apps
$ nano settings.py
```
 Then insert the following in the settings.py file:
 ```
  GEOSERVER_URL_BASE = 'http://domainname.com:8181' (Insert your geoserver url here)
  GEOSERVER_URL_SSL_BASE = 'https://domainname.com:8443' (For HTTPS only)
  GEOSERVER_USER_NAME = 'admin' (Insert your geoserver user name) 
  GEOSERVER_USER_PASSWORD = 'geoserver' (Insert your geoserver password)
```
  Save File: Ctrl + X. When prompted, Press Y.

#### Enable CORS on geoserver

##### For Tethys 1.3
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
##### For Tethys 1.4
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

##Updating the App:
Update the local repository and Tethys Platform instance.
```
$ . /usr/lib/tethys/bin/activate
$ cd servirdi
$ git stash
$ git pull
```

Restart the Apache Server:
See: http://docs.tethysplatform.org/en/latest/production/installation.html#enable-site-and-restart-apache
