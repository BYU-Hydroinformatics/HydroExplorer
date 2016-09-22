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
    var map,
        layers,
        element,
        popup,
        wmsLayer,
        wmsSource,
        current_layer,
        layersDict,
        ContextMenuBase;
    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/
    var init_map,
        init_menu,
        init_jquery_var,
        init_events,
        add_server,
        addContextMenuToListItem,
        $modalAddHS,
        onClickZoomTo,
        onClickDeleteLayer,
        $hs_list,
        location_search,
        generate_graph;

    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/

    init_map = function(){
        var projection = ol.proj.get('EPSG:3857');
        var baseLayer = new ol.layer.Tile({
            source: new ol.source.BingMaps({
                key: '5TC0yID7CYaqv3nVQLKe~xWVt4aXWMJq2Ed72cO4xsA~ApdeyQwHyH_btMjQS1NJ7OHKY8BK-W-EMQMrIavoQUMYXeZIQOUURnKGBOC7UCt4',
                imagerySet: 'AerialWithLabels' // Options 'Aerial', 'AerialWithLabels', 'Road'
            })
        });

        var fullScreenControl = new ol.control.FullScreen();
        var view = new ol.View({
            center: [-11500000, 4735000],
            projection: projection,
            zoom: 4
        });
        layers = [baseLayer];
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

    };
    init_jquery_var = function () {
        //$('#current-servers').empty();
        $modalAddHS = $('#modalAddHS');
        $hs_list = $('#current-servers-list');
    };
    add_server = function(){
        var datastring = $modalAddHS.serialize();
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
                    wmsSource = new ol.source.TileWMS({
                        url: rest_url,
                        params: {'LAYERS':wms_url},
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

        map.on("singleclick",function(evt){
            //Check for each layer in the baselayers

            $(element).popover('destroy');

            if (map.getTargetElement().style.cursor == "pointer") {
                var clickCoord = evt.coordinate;
                popup.setPosition(clickCoord);

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
                            var details_html = "/apps/servir/details/?sitename="+site_name+"&sitecode="+site_code+"&network="+network+"&hsurl="+hs_url+"&hidenav=true";

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


            }


        });

        $('#close-modalViewDetails').on('click', function () {
            $('#modalViewDetails').modal('hide');
        });

        map.on('pointermove', function(evt) {
            if (evt.dragging) {
                return;
            }
            var pixel = map.getEventPixel(evt.originalEvent);
            var hit = map.forEachLayerAtPixel(pixel, function(layer) {
                if (layer != layers[0]){
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
        var variable = $('#select_var option:selected').val();
        $.ajax({
            type: "GET",
            url: '/apps/servir/api/',
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
                console.log(Error);
            }
        });

    };
    $('#generate-graph').on('click',generate_graph);

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


    /************************************************************************
     *                  INITIALIZATION / CONSTRUCTOR
     *************************************************************************/
    $(function () {
        init_map();
        init_jquery_var();
        init_events();
        init_menu();
    });

}()); // End of package wrapper

