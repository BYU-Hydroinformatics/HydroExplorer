/*****************************************************************************
 * FILE:      Main.js
 * DATE:      8 August 2016
 * AUTHOR:    Sarva Pulla
 * COPYRIGHT: (c) Brigham Young University 2016
 * LICENSE:   BSD 2-Clause
 *
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var SERVIR_PACKAGE = (function() {
    // Wrap the library in a package function
    "use strict"; // And enable strict mode for this library


    /************************************************************************
     *                      MODULE LEVEL / GLOBAL VARIABLES
     *************************************************************************/
    var ContextMenuBase,
        colors,
        current_layer,
        element,
        layers,
        layersDict,
        map,
        popup,
        wmsLayer,
        wmsSource;
    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/
    var addContextMenuToListItem,
        add_server,
        add_soap,
        click_catalog,
        generate_graph,
        generate_plot,
        get_data_rods,
        get_his_server,
        get_hs_list,
        get_random_color,
        init_cluster,
        init_map,
        init_menu,
        init_jquery_var,
        init_events,
        load_catalog,
        location_search,
        $modalAddHS,
        $modalAddSOAP,
        set_color,
        $SoapVariable,
        $modalHIS,
        $modalDelete,
        $modalDataRods,
        $modalInterface,
        onClickZoomTo,
        onClickDeleteLayer,
        $hs_list,
        update_catalog;

    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/

    colors = ['#ff0000','#0033cc','#000099','#ff0066','#ff00ff','#800000','#6699ff','#6600cc','#00ffff'];
    set_color = function(){
        var color = colors[Math.floor(Math.random() * colors.length)];
        return color;
    };
    get_random_color = function() {
        var letters = '012345'.split('');
        var color = '#';
        color += letters[Math.round(Math.random() * 5)];
        letters = '0123456789ABCDEF'.split('');
        for (var i = 0; i < 5; i++) {
            color += letters[Math.round(Math.random() * 15)];
        }
        return color;
    };
    init_map = function(){
        var projection = ol.proj.get('EPSG:3857');
        var baseLayer = new ol.layer.Tile({
            source: new ol.source.BingMaps({
                key: '5TC0yID7CYaqv3nVQLKe~xWVt4aXWMJq2Ed72cO4xsA~ApdeyQwHyH_btMjQS1NJ7OHKY8BK-W-EMQMrIavoQUMYXeZIQOUURnKGBOC7UCt4',
                imagerySet: 'AerialWithLabels' // Options 'Aerial', 'AerialWithLabels', 'Road'
            })
        });
        var image = new ol.style.Circle({
            radius: 7,
            fill: new ol.style.Fill({
                color: 'rgba(255, 0, 0, 0.7)'
            }),
            stroke: new ol.style.Stroke({color: 'red', width: 1})
        });

        var pointSource = new ol.source.Vector();

        var pointLayer = new ol.layer.Vector({
            source: pointSource,
            style: new ol.style.Style({
                image: image
            })
        });

        var fullScreenControl = new ol.control.FullScreen();
        var view = new ol.View({
            center: [-11500000, 4735000],
            projection: projection,
            zoom: 4
        });
        layers = [baseLayer,pointLayer];
        //Declare the map object itself.
        layersDict = {};

        map = new ol.Map({
            target: document.getElementById("map"),
            layers: layers,
            view: view
        });

        //Zoom slider
        map.addControl(new ol.control.ZoomSlider());
        map.addControl(fullScreenControl);
        map.crossOrigin = 'anonymous';
        element = document.getElementById('popup');

        popup = new ol.Overlay({
            element: element,
            positioning: 'bottom-center',
            stopEvent: true
        });
        map.addOverlay(popup);
        init_events();
    };

    init_jquery_var = function () {
        //$('#current-servers').empty();
        $modalAddHS = $('#modalAddHS');
        $modalAddSOAP = $('#modalAddSoap');
        $SoapVariable = $('#soap_variable');
        $modalDelete = $('#modalDelete');
        $modalHIS = $('#modalHISCentral');
        $modalDataRods = $('#modalDataRods');
        $modalInterface = $('#modalInterface');
        $hs_list = $('#current-servers-list');
    };

    $(".settings").click(function(){
        $modalInterface.find('.success').html('');
    });

    init_cluster = function(layer_source){
        var clusterSource = new ol.source.Cluster({
            distance: 10,
            source: layer_source
        });
        var styleCache = {};
        var clusters = new ol.layer.Vector({
            source: clusterSource,
            style: function(feature) {
                var size = feature.get('features').length;
                var style = styleCache[size];
                if (!style) {
                    style = new ol.style.Style({
                        image: new ol.style.Circle({
                            radius: 10,
                            stroke: new ol.style.Stroke({
                                color: '#fff'
                            }),
                            fill: new ol.style.Fill({
                                color: '#3399CC'
                            })
                        }),
                        text: new ol.style.Text({
                            text: size.toString(),
                            fill: new ol.style.Fill({
                                color: '#fff'
                            })
                        })
                    });
                    styleCache[size] = style;
                }
                return style;
            }
        });
        map.addLayer(clusters);
    };

    get_his_server = function () {
        var datastring = $modalHIS.serialize();
        $.ajax({
            type: "POST",
            url: '/apps/servir/his-server/',
            data:datastring,
            dataType: 'HTML',
            success: function (result) {
                var json_response = JSON.parse(result);
                var url = json_response.url;
                $('#soap-url').val(url);
                $('#modalHISCentral').modal('hide');

                $( '#modalHISCentral' ).each(function(){
                    this.reset();
                });
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                console.log(Error);
            }
        });
    };
    $("#add-from-his").on('click',get_his_server);



    get_data_rods = function () {
        if (($("#gldas-lat-lon").val()=="")){
            $modalDataRods.find('.warning').html('<b>Please select a point on the map.</b>');
            return false;
        }
        if (($("#gldas-lat-lon").val()!= "")){
            $modalDataRods.find('.warning').html('');
        }
        $('#modalDataRods').modal('hide');

        var datastring = $modalDataRods.serialize();
        var details_url = "/apps/servir/datarods/?"+datastring;
        var $loading = $('#view-gldas-loading');
        $('#gldas-container').addClass('hidden');
        $loading.removeClass('hidden');

        $('#gldas-container')
            .empty()
            .append('<iframe id="gldas-viewer" src="' + details_url + '" allowfullscreen></iframe>');
        $('#modalViewRods').modal('show');
        $('#gldas-viewer').one('load', function () {
            $loading.addClass('hidden');
            $('#gldas-container').removeClass('hidden');
            $loading.addClass('hidden');
        });


    };
    $("#get-data-rods").on('click',get_data_rods);

    get_hs_list = function(){
        $.ajax({
            type: "GET",
            url: '/apps/servir/catalog/',
            dataType: 'JSON',
            success: function (result) {
                var server = result['hydroserver'];
                var HSTableHtml = '<table id="tbl-hydroservers"><thead><th></th><th>Title</th><th>URL</th></thead><tbody>';
                if (server.length === 0) {
                    $modalDelete.find('.modal-body').html('<b>There are no hydroservers in the Catalog.</b>');
                } else{
                    for (var i = 0; i < server.length; i++) {
                        var title = server[i].title;
                        var url = server[i].url;
                        var geoserver_url = server[i].geoserver_url;
                        var layer_name = server[i].layer_name;
                        var extents = server[i].extents;
                        HSTableHtml += '<tr>' +
                            '<td><input type="radio" name="server" id="server" value="' + title + '"></td>' +
                            '<td class="hs_title">' + title + '</td>' +
                            '<td class="hs_url">' + url + '</td>' +
                            '</tr>';
                    }
                    HSTableHtml += '</tbody></table>';
                    $modalDelete.find('.modal-body').html(HSTableHtml);
                }


            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                console.log(Error);
            }

        });
    };
    $("#delete-server").on('click',get_hs_list);

    load_catalog = function () {
        $.ajax({
            type: "GET",
            url: '/apps/servir/catalog/',
            dataType: 'JSON',
            success: function (result) {
                var servers = result['hydroserver'];
                $('#current-servers').empty();
                servers.forEach(function (server) {
                    var title = server.title;
                    var url = server.url;
                    var geoserver_url = server.geoserver_url;
                    var layer_name = server.layer_name;
                    var extents = server.extents;
                    $('<li class="ui-state-default"' + 'layer-name="' + title + '"' + '><input class="chkbx-layer" type="checkbox" checked><span class="server-name">' + title + '</span><div class="hmbrgr-div"><img src="/static/servir/images/hamburger.svg"></div></li>').appendTo('#current-servers');
                    addContextMenuToListItem($('#current-servers').find('li:last-child'));
                    var sld_string = '<StyledLayerDescriptor version="1.0.0"><NamedLayer><Name>'+layer_name+'</Name><UserStyle><FeatureTypeStyle><Rule><PointSymbolizer><Graphic><Mark><WellKnownName>circle</WellKnownName><Fill><CssParameter name="fill">'+set_color()+'</CssParameter></Fill></Mark><Size>10</Size></Graphic></PointSymbolizer></Rule></FeatureTypeStyle></UserStyle></NamedLayer></StyledLayerDescriptor>';
                    wmsSource = new ol.source.TileWMS({
                        url: geoserver_url,
                        params: {'LAYERS':layer_name,
                            'SLD_BODY':sld_string},
                        serverType: 'geoserver',
                        crossOrigin: 'Anonymous'
                    });
                    wmsLayer = new ol.layer.Tile({
                        extent:ol.proj.transformExtent([extents['minx'],extents['miny'],extents['maxx'],extents['maxy']],'EPSG:4326','EPSG:3857'),
                        source: wmsSource
                    });

                    map.addLayer(wmsLayer);

                    layersDict[title] = wmsLayer;
                    var layer_extent = wmsLayer.getExtent();
                    map.getView().fit(layer_extent,map.getSize());

                });

                // rand_lyr.getSource().changed();
                // var layer_extent = layersDict[Object.keys(layersDict)[0]].getExtent();
                // Object.keys(layersDict).forEach(function (key) {
                //     var layer_extent = layersDict[key].getExtent();
                //     map.getView().fit(layer_extent,map.getSize());
                // });
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                console.log(Error);
            }

        });


    };



    update_catalog = function () {
        $modalInterface.find('.success').html('');
        var datastring = $modalDelete.serialize();
        $.ajax({
            type: "POST",
            url: '/apps/servir/delete/',
            data: datastring,
            dataType: 'HTML',
            success: function (result) {
                var json_response = JSON.parse(result);
                var title = json_response.title;
                $('#current-servers').empty();
                $('#modalDelete').modal('hide');

                //map.addLayer(new_layer);
                $( '#modalDelete' ).each(function(){
                    this.reset();
                });

                map.removeLayer(layersDict[title]);
                delete layersDict[title];
                map.updateSize();
                load_catalog();
                click_catalog();
                $modalInterface.find('.success').html('<b>Successfully Updated the Catalog!</b>');
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                console.log(Error);
            }

        });

    };
    $("#btn-del-server").on('click',update_catalog);

    add_server = function(){
        var datastring = $modalAddHS.serialize();
        if(($("#hs-title").val())==""){
            $modalAddSOAP.find('.warning').html('<b>Please enter a title. This field cannot be blank.</b>');
            return false;
        }else{
            $modalAddSOAP.find('.warning').html('');
        }
        if(($("#hs-url").val())==""){
            $modalAddSOAP.find('.warning').html('<b>Please enter a valid URL. This field cannot be blank.</b>');
            return false;
        }else{
            $modalAddSOAP.find('.warning').html('');
        }
        if(($("#hs-title").val()) != ""){
            var regex = new RegExp("^[a-zA-Z ]+$");
            var title = $("#soap-title").val();
            if (!regex.test(title)) {
                $modalAddSOAP.find('.warning').html('<b>Please enter Letters only for the title.</b>');
                return false;
            }
        }else{
            $modalAddSOAP.find('.warning').html('');
        }
        // if(($("#hs-code").val())==""){
        //     alert("Please enter a Code for the site.");
        //     return false;
        // }
        // if(($("#hs-website").val())==""){
        //     alert("Please enter a Website for the Organization.");
        //     return false;
        // }
        // if(($("#hs-citation").val())==""){
        //     alert("Please enter a Citation for the source.");
        //     return false;
        // }
        // if(($("#hs-contact").val())==""){
        //     alert("Please enter a Contact for the Organization.");
        //     return false;
        // }
        // if(($("#hs-abstract").val())==""){
        //     alert("Please enter an Abstract for the Source.");
        //     return false;
        // }
        // if(($("#hs-email").val())==""){
        //     alert("Please enter an Email for the Contact.");
        //     return false;
        // }

        $.ajax({
            type: "POST",
            url: '/apps/servir/add-server/',
            dataType: 'HTML',
            data: datastring,
            success: function(result)
            {
                var json_response = JSON.parse(result);
                if (json_response.status === 'true')
                {
                    var title= json_response.title;
                    var wms_url = json_response.wms;
                    var extents = json_response.bounds;
                    var rest_url = json_response.rest_url;


                    $('<li class="ui-state-default"'+'layer-name="'+title+'"'+'><input class="chkbx-layer" type="checkbox" checked><span class="server-name">'+title+'</span><div class="hmbrgr-div"><img src="/static/servir/images/hamburger.svg"></div></li>').appendTo('#current-servers');

                    addContextMenuToListItem($('#current-servers').find('li:last-child'));

                    $('#modalAddHS').modal('hide');

                    //map.addLayer(new_layer);
                    $( '#modalAddHS' ).each(function(){
                        this.reset();
                    });
                    var sld_string = '<StyledLayerDescriptor version="1.0.0"><NamedLayer><Name>'+wms_url+'</Name><UserStyle><FeatureTypeStyle><Rule><PointSymbolizer><Graphic><Mark><WellKnownName>circle</WellKnownName><Fill><CssParameter name="fill">'+set_color()+'</CssParameter></Fill></Mark><Size>10</Size></Graphic></PointSymbolizer></Rule></FeatureTypeStyle></UserStyle></NamedLayer></StyledLayerDescriptor>';
                    wmsSource = new ol.source.TileWMS({
                        url: rest_url,
                        params: {'LAYERS':wms_url,
                            'SLD_BODY':sld_string},
                        serverType: 'geoserver',
                        crossOrigin: 'Anonymous'
                    });
                    wmsLayer = new ol.layer.Tile({
                        extent:ol.proj.transformExtent([extents['minx'],extents['miny'],extents['maxx'],extents['maxy']],'EPSG:4326','EPSG:3857'),
                        source: wmsSource
                    });

                    map.addLayer(wmsLayer);

                    layersDict[title] = wmsLayer;

                    var layer_extent = wmsLayer.getExtent();
                    map.getView().fit(layer_extent,map.getSize());
                }
                else{
                    alert("Please Check your URL and Try Again.");
                }

            },
            error: function(XMLHttpRequest, textStatus, errorThrown)
            {
                console.log(Error);
            }
        });

    };

    $('#btn-add-server').on('click', add_server);

    add_soap = function () {
        $modalInterface.find('.success').html('');
        if(($("#extent")).is(':checked')){
            var zoom = map.getView().getZoom();
            if (zoom < 8){
                $modalAddSOAP.find('.warning').html('<b>The zoom level has to be 8 or greater. Please check and try again.</b>');
                return false;
            }else{
                $modalAddSOAP.find('.warning').html('');
            }
            $("#chk_val").empty();
            var level = map.getView().calculateExtent(map.getSize());
            $('<input type="text" name="extent_val" id="extent_val" value='+'"'+level+'"'+' hidden>').appendTo($("#chk_val"));
            // $(this).val(level);
        }
        if(($("#soap-title").val())==""){
            $modalAddSOAP.find('.warning').html('<b>Please enter a title. This field cannot be blank.</b>');
            return false;
        }else{
            $modalAddSOAP.find('.warning').html('');
        }
        if(($("#soap-url").val())==""){
            $modalAddSOAP.find('.warning').html('<b>Please enter a valid URL. This field cannot be blank.</b>');
            return false;
        }else{
            $modalAddSOAP.find('.warning').html('');
        }
        if(($("#soap-title").val()) != ""){
            var regex = new RegExp("^[a-zA-Z ]+$");
            var title = $("#soap-title").val();
            if (!regex.test(title)) {
                $modalAddSOAP.find('.warning').html('<b>Please enter Letters only for the title.</b>');
                return false;
            }
        }else{
            $modalAddSOAP.find('.warning').html('');
        }
        var datastring = $modalAddSOAP.serialize();
        $.ajax({
            type: "POST",
            url: '/apps/servir/soap/',
            dataType: 'HTML',
            data: datastring,
            success: function(result)
            {
                var json_response = JSON.parse(result);
                if (json_response.status === 'true')
                {

                    var title= json_response.title;
                    var wms_url = json_response.wms;
                    var extents = json_response.bounds;
                    var rest_url = json_response.rest_url;
                    var zoom = json_response.zoom;

                    if (zoom == 'true'){
                        var level = json_response.level;
                    }

                    $('<li class="ui-state-default"'+'layer-name="'+title+'"'+'><input class="chkbx-layer" type="checkbox" checked><span class="server-name">'+title+'</span><div class="hmbrgr-div"><img src="/static/servir/images/hamburger.svg"></div></li>').appendTo('#current-servers');

                    addContextMenuToListItem($('#current-servers').find('li:last-child'));

                    $('#modalAddSoap').modal('hide');

                    //map.addLayer(new_layer);
                    $( '#modalAddSoap' ).each(function(){
                        this.reset();
                    });
                    var sld_string = '<StyledLayerDescriptor version="1.0.0"><NamedLayer><Name>'+wms_url+'</Name><UserStyle><FeatureTypeStyle><Rule><PointSymbolizer><Graphic><Mark><WellKnownName>circle</WellKnownName><Fill><CssParameter name="fill">'+set_color()+'</CssParameter></Fill></Mark><Size>10</Size></Graphic></PointSymbolizer></Rule></FeatureTypeStyle></UserStyle></NamedLayer></StyledLayerDescriptor>';
                    wmsSource = new ol.source.TileWMS({
                        url: rest_url,
                        params: {'LAYERS':wms_url,
                            'SLD_BODY':sld_string},
                        serverType: 'geoserver',
                        crossOrigin: 'Anonymous'
                    });
                    wmsLayer = new ol.layer.Tile({
                        extent:ol.proj.transformExtent([extents['minx'],extents['miny'],extents['maxx'],extents['maxy']],'EPSG:4326','EPSG:3857'),
                        source: wmsSource
                    });

                    map.addLayer(wmsLayer);

                    layersDict[title] = wmsLayer;

                    var layer_extent = wmsLayer.getExtent();
                    map.getView().fit(layer_extent,map.getSize());
                    $modalInterface.find('.success').html('<b>Successfully Added the HydroServer to the Map!</b>');
                }
                else{
                    $modalAddSOAP.find('.warning').html('<b>Failed to add server. Please check Url and try again.</b>');
                }

            },
            error: function(XMLHttpRequest, textStatus, errorThrown)
            {
                $modalAddSOAP.find('.warning').html('<b>Invalid Hydroserver SOAP Url. Please check and try again.</b>');
                if(($("#extent")).is(':checked')){
                    $modalAddSOAP.find('.warning').html('<b>The requested area does not have any sites. Please try another area.</b>');
                    return false;
                }else{
                    $modalAddSOAP.find('.warning').html('');
                }

            }
        });

    };
    $('#btn-add-soap').on('click', add_soap);



    location_search = function(){
        function geocoder_success(results, status) {
            if (status == google.maps.GeocoderStatus.OK) {
                var r=results;
                var flag_geocoded=true;
                var Lat = results[0].geometry.location.lat();
                var Lon = results[0].geometry.location.lng();
                var dbPoint = {
                    "type": "Point",
                    "coordinates": [Lon, Lat]
                };

                var coords = ol.proj.transform(dbPoint.coordinates, 'EPSG:4326','EPSG:3857');
                map.getView().setCenter(coords);
                map.getView().setZoom(12);
            } else {
                alert("Geocode was not successful for the following reason: " + status);
            }
        }
        var g = new google.maps.Geocoder();
        var search_location = document.getElementById('location_input').value;
        g.geocode({'address':search_location},geocoder_success);

    };
    $('#location_search').on('click',location_search);

    onClickZoomTo = function(e){
        var clickedElement = e.trigger.context;
        var $lyrListItem = $(clickedElement).parent().parent();
        var layer_name = $lyrListItem.attr('layer-name');
        var layer_extent = layersDict[layer_name].getExtent();
        map.getView().fit(layer_extent,map.getSize());
    };
    onClickDeleteLayer = function(e){
        var clickedElement = e.trigger.context;
        var $lyrListItem = $(clickedElement).parent().parent();
        var layer_name = $lyrListItem.attr('layer-name');
        map.removeLayer(layersDict[layer_name]);
        delete layersDict[layer_name];
        $lyrListItem.remove();
    };

    init_events = function(){
        (function () {
            var target, observer, config;
            // select the target node
            target = $('#app-content-wrapper')[0];

            observer = new MutationObserver(function () {
                window.setTimeout(function () {
                    map.updateSize();
                }, 350);
            });
            $(window).on('resize', function () {
                map.updateSize();
            });

            config = {attributes: true};

            observer.observe(target, config);
        }());
        $(document).on('change', '.chkbx-layer', function () {
            var displayName = $(this).next().text();
            layersDict[displayName].setVisible($(this).is(':checked'));
        });

        // $(document).ajaxStart($.blockUI).ajaxStop($.unblockUI);
        map.on("moveend", function() {
            var zoom = map.getView().getZoom();
            var zoomInfo = '<h6>Current Zoom level = ' + zoom+'</h6>';
            document.getElementById('zoomlevel').innerHTML = zoomInfo;
            Object.keys(layersDict).forEach(function(key){
                var source =  layersDict[key].getSource();
            });
        });
        map.on("singleclick",function(evt){
            //Check for each layer in the baselayers

            $(element).popover('destroy');


            if (map.getTargetElement().style.cursor == "pointer") {
                var clickCoord = evt.coordinate;
                popup.setPosition(clickCoord);
                // map.getLayers().item(1).getSource().clear();

                var view = map.getView();
                var viewResolution = view.getResolution();
                var wms_url = current_layer.getSource().getGetFeatureInfoUrl(evt.coordinate, viewResolution, view.getProjection(), {'INFO_FORMAT': 'application/json'});
                if (wms_url) {
                    $.ajax({
                        type: "GET",
                        url: wms_url,
                        dataType: 'json',
                        success: function (result) {
                            var site_name = result["features"][0]["properties"]["sitename"];
                            var site_code = result["features"][0]["properties"]["sitecode"];
                            var network = result["features"][0]["properties"]["network"];
                            var hs_url = result["features"][0]["properties"]["url"];
                            var service = result["features"][0]["properties"]["service"];
                            var details_html = "/apps/servir/details/?sitename="+site_name+"&sitecode="+site_code+"&network="+network+"&hsurl="+hs_url+"&service="+service+"&hidenav=true";

                            $(element).popover({
                                'placement': 'top',
                                'html': true,
                                // 'content': '<b>Name:</b>'+site_name+'<br><b>Code:</b>'+site_code+'<br><button type="button" class="mod_link btn-primary" data-html="'+details_html+'" >Site Details</button>'
                                'content':'<table border="1"><tbody><tr><th>Site Name</th><th>Site Id</th><th>Details</th></tr>'+'<tr><td>'+site_name +'</td><td>'+ site_code + '</td><td><button type="button" class="mod_link btn-primary" data-html="'+details_html+'" >Site Details</button></td></tr>'
                            });

                            $(element).popover('show');
                            $(element).next().css('cursor', 'text');
                            $('.mod_link').on('click',function(){
                                var $loading = $('#view-file-loading');
                                $('#iframe-container').addClass('hidden');
                                $loading.removeClass('hidden');
                                var details_url = $(this).data('html');
                                $('#iframe-container')
                                    .empty()
                                    .append('<iframe id="iframe-details-viewer" src="' + details_url + '" allowfullscreen></iframe>');
                                $('#modalViewDetails').modal('show');
                                $('#iframe-details-viewer').one('load', function () {
                                    $loading.addClass('hidden');
                                    $('#iframe-container').removeClass('hidden');
                                    $loading.addClass('hidden');
                                });
                            });
                        },
                        error: function (XMLHttpRequest, textStatus, errorThrown) {
                            console.log(Error);
                        }
                    });
                }


            }else{
                var coords = evt.coordinate;
                var proj_coords = ol.proj.transform(coords, 'EPSG:3857','EPSG:4326');
                var geojsonObject = {
                    'type': 'FeatureCollection',
                    'crs': {
                        'type': 'name',
                        'properties': {
                            'name': 'EPSG:3857'
                        }
                    },
                    'features': [{
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': coords
                        }
                    }]
                };
                var ptSource = map.getLayers().item(1).getSource();
                ptSource.clear();
                ptSource.addFeatures((new ol.format.GeoJSON()).readFeatures(geojsonObject));
                $("#gldas-lat-lon").val(proj_coords);
                console.log(proj_coords);
                if (($("#gldas-lat-lon").val()!= "")){
                    $modalDataRods.find('.warning').html('');
                }
            }


        });

        $('#close-modalViewDetails').on('click', function () {
            $('#modalViewDetails').modal('hide');
        });
        $('#close-modalViewRods').on('click', function () {
            $('#modalViewRods').modal('hide');
        });


        map.on('pointermove', function(evt) {
            if (evt.dragging) {
                return;
            }
            var pixel = map.getEventPixel(evt.originalEvent);
            var hit = map.forEachLayerAtPixel(pixel, function(layer) {
                if (layer != layers[0] && layer != layers[1]){
                    current_layer = layer;
                    return true;}
            });
            map.getTargetElement().style.cursor = hit ? 'pointer' : '';
        });


    };
    init_menu = function(){
        ContextMenuBase = [
            {
                name: 'Zoom To',
                title: 'Zoom To',
                fun: function (e) {
                    onClickZoomTo(e);
                }
            },
            {
                name: 'Delete',
                title: 'Delete',
                fun: function (e) {
                    onClickDeleteLayer(e);
                }
            }
        ];
    };

    generate_graph = function(){
        $(document).find('.warning').html('');
        var variable = $('#select_var option:selected').val();

        $.ajax({
            type: "GET",
            url: '/apps/servir/rest-api/',
            dataType: 'JSON',
            success: function (result) {

                for (var i=0;i < result['graph'].length;i++){
                    if (result['graph'][i]['variable'] == variable){
                        $('#container').highcharts({
                            chart: {
                                type:'area',
                                zoomType: 'x'
                            },
                            title: {
                                text: result['graph'][i]['title'],
                                style: {
                                    fontSize: '11px'
                                }
                            },
                            xAxis: {
                                type: 'datetime',
                                labels: {
                                    format: '{value:%d %b %Y}',
                                    rotation: 45,
                                    align: 'left'
                                },
                                title: {
                                    text: 'Date'
                                }
                            },
                            yAxis: {
                                title: {
                                    text: result['graph'][i]['unit']
                                }

                            },
                            exporting: {
                                enabled: true,
                                width: 5000
                            },
                            series: [{
                                data: result['graph'][i]['values'],
                                name: result['graph'][i]['variable']
                            }]

                        });

                    }

                }

            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                $(document).find('.warning').html('<b>Unable to generate graph. Please check the start and end dates and try again.</b>');
                console.log(Error);
            }
        });

    };

    $('#generate-graph').on('click',generate_graph);
    generate_plot = function(){
        var datastring = $SoapVariable.serialize();
        $.ajax({
            type: "POST",
            url: '/apps/servir/soap-api/',
            dataType: 'JSON',
            data: datastring,
            success: function(result){
                $('#plotter').highcharts({
                    chart: {
                        type:'area',
                        zoomType: 'x'
                    },
                    title: {
                        text: result['title'],
                        style: {
                            fontSize: '11px'
                        }
                    },
                    xAxis: {
                        type: 'datetime',
                        labels: {
                            format: '{value:%d %b %Y}',
                            rotation: 45,
                            align: 'left'
                        },
                        title: {
                            text: 'Date'
                        }
                    },
                    yAxis: {
                        title: {
                            text: result['unit']
                        }

                    },
                    exporting: {
                        enabled: true,
                        width: 5000
                    },
                    series: [{
                        data: result['values'],
                        name: result['variable']
                    }]

                });
            },
            error: function(XMLHttpRequest, textStatus, errorThrown)
            {
                $(document).find('.warning').html('<b>Unable to generate graph. Please check the start and end dates and try again.</b>');
                console.log(Error);
            }
        });
        return false;
    };

    $('#generate-plot').on('click',generate_plot);

    addContextMenuToListItem = function ($listItem) {
        var contextMenuId;

        $listItem.find('.hmbrgr-div img')
            .contextMenu('menu', ContextMenuBase, {
                'triggerOn': 'click',
                'displayAround': 'trigger',
                'mouseClick': 'left',
                'position': 'right',
                'onOpen': function (e) {
                    $('.hmbrgr-div').removeClass('hmbrgr-open');
                    $(e.trigger.context).parent().addClass('hmbrgr-open');
                },
                'onClose': function (e) {
                    $(e.trigger.context).parent().removeClass('hmbrgr-open');
                }
            });
        contextMenuId = $('.iw-contextMenu:last-child').attr('id');
        $listItem.attr('data-context-menu', contextMenuId);
    };

    click_catalog = function(){
        $('.iw-contextMenu').find('[title="Zoom To"]').each(function (index, obj) {
            obj.click();
        });
        map.updateSize();
    };



    /************************************************************************
     *                  INITIALIZATION / CONSTRUCTOR
     *************************************************************************/
    $(function () {

        init_jquery_var();
        init_menu();
        init_map();
        load_catalog();
        setTimeout(click_catalog,1000);
    });

}()); // End of package wrapper

