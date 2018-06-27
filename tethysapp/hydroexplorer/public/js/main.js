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

var staticPath = baseStatic;
var apiServer = `${staticPath.replace('\/static','\/apps')}`;

window.onbeforeunload = null;

var HYDROEXPLORER_PACKAGE = (function() {
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
        layersDict, //Dictionary for keeping track of the new layers that are being added to the map
        map,
        popup,
        shpSource,
        shpLayer,
        wmsLayer,
        wmsSource;
    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/
    var addContextMenuToListItem,
        add_server,
        add_soap,
        addDefaultBehaviorToAjax,
        checkCsrfSafe,
        getCookie,
        click_catalog,
        clear_coords,
        generate_graph,
        generate_plot,
        get_climate_serv,
        get_data_rods,
        get_his_server,
        get_hs_list,
        get_random_color,
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
        $modalClimate,
        $modalDelete,
        $modalDataRods,
        $modalInterface,
        $modalUpload,
        $btnUpload,
        onClickZoomTo,
        onClickDeleteLayer,
        $hs_list,
        prepare_files,
        update_catalog,
        upload_file,
        createExportCanvas;

    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS : How are these private? JS has no concept of that
     *************************************************************************/

    colors = ['#ff0000', '#0033cc', '#000099', '#ff0066', '#ff00ff', '#800000', '#6699ff', '#6600cc', '#00ffff']; // List of colors for generating the styling of the points on the map
    set_color = function() {
        var color = colors[Math.floor(Math.random() * colors.length)];
        return color;
    }; // Return a random color from the list of colors
    clear_coords = function() {
        $("#poly-lat-lon").val('');
        $("#point-lat-lon").val('');
    }; //Clear the point/polygon coordinates so that its easier for the post request to process the form
    get_random_color = function() {
        var letters = '012345'.split('');
        var color = '#';
        color += letters[Math.round(Math.random() * 5)];
        letters = '0123456789ABCDEF'.split('');
        for (var i = 0; i < 5; i++) {
            color += letters[Math.round(Math.random() * 15)];
        }
        return color;
    }; // Leaving this here as it is pretty neat snippet of code
    init_map = function() {

        var projection = ol.proj.get('EPSG:3857');
        var baseLayer = new ol.layer.Tile({
            source: new ol.source.BingMaps({
                key: '5TC0yID7CYaqv3nVQLKe~xWVt4aXWMJq2Ed72cO4xsA~ApdeyQwHyH_btMjQS1NJ7OHKY8BK-W-EMQMrIavoQUMYXeZIQOUURnKGBOC7UCt4',
                imagerySet: 'AerialWithLabels' // Options 'Aerial', 'AerialWithLabels', 'Road'
            })
        });

        //Creating an empty source and layer to store the shapefile geojson object
        shpSource = new ol.source.Vector();
        shpLayer = new ol.layer.Vector({
            source: shpSource
        });

        //Creating an empty source and layer to store the point/polygon features.
        var source = new ol.source.Vector({
            wrapX: false
        });
        var vector_layer = new ol.layer.Vector({
            name: 'my_vectorlayer',
            source: source,
            style: new ol.style.Style({
                fill: new ol.style.Fill({
                    color: 'rgba(255, 255, 255, 0.2)'
                }),
                stroke: new ol.style.Stroke({
                    color: '#ffcc33',
                    width: 2
                }),
                image: new ol.style.Circle({
                    radius: 7,
                    fill: new ol.style.Fill({
                        color: '#ffcc33'
                    })
                })
            })
        });
        var fullScreenControl = new ol.control.FullScreen();
        var view = new ol.View({
            center: [-11500000, 4735000],
            projection: projection,
            zoom: 4
        });
        layers = [baseLayer, vector_layer, shpLayer];

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

        var lastFeature, draw, featureType;

        //Remove the last feature before drawing a new one
        var removeLastFeature = function() {
            if (lastFeature) source.removeFeature(lastFeature);
        };

        //Add the point/polygon interaction to the map
        var addInteraction = function(geomtype) {
            var typeSelect = document.getElementById('types');
            var value = typeSelect.value;
            $('#data').val('');
            if (value !== 'None') {
                if (draw)
                    map.removeInteraction(draw);

                draw = new ol.interaction.Draw({
                    source: source,
                    type: geomtype
                });


                map.addInteraction(draw);
            }
            if (featureType === 'Point' || featureType === 'Polygon') {

                // draw.on('drawend', function (e) {
                //     removeLastFeature();
                //     lastFeature = e.feature;
                // });
                draw.on('drawend', function(e) {
                    lastFeature = e.feature;

                });

                draw.on('drawstart', function(e) {
                    source.clear();
                });

            }


        };

        //Extracting information from the saved json object data
        vector_layer.getSource().on('addfeature', function(event) {
            var feature_json = saveData();
            var parsed_feature = JSON.parse(feature_json);
            var feature_type = parsed_feature["features"][0]["geometry"]["type"];

            //Save the point values to the point-lat-lon field
            if (feature_type == 'Point') {
                var coords = parsed_feature["features"][0]["geometry"]["coordinates"];
                var proj_coords = ol.proj.transform(coords, 'EPSG:3857', 'EPSG:4326');
                $("#gldas-lat-lon").val(proj_coords);
                $modalDataRods.modal('show');

            } else if (feature_type == 'Polygon') {
                //Save the coordinates to the cserv-lat-lon field
                $modalClimate.modal('show');
                var coords = parsed_feature["features"][0]["geometry"]["coordinates"][0];
                proj_coords = [];
                coords.forEach(function(coord) {
                    var transformed = ol.proj.transform(coord, 'EPSG:3857', 'EPSG:4326');
                    proj_coords.push('[' + transformed + ']');
                });
                var json_object = '{"type":"Polygon","coordinates":[[' + proj_coords + ']]}';
                $("#cserv_lat_lon").val(json_object);
            }
        });

        //Save the drawn feature as a json object
        function saveData() {
            // get the format the user has chosen
            var data_type = 'GeoJSON',
                // define a format the data shall be converted to
                format = new ol.format[data_type](),
                // this will be the data in the chosen format
                data;
            try {
                // convert the data of the vector_layer into the chosen format
                data = format.writeFeatures(vector_layer.getSource().getFeatures());
            } catch (e) {
                // at time of creation there is an error in the GPX format (18.7.2014)
                $('#data').val(e.name + ": " + e.message);
                return;
            }
            // $('#data').val(JSON.stringify(data, null, 4));
            return data;

        }

        //Change the map based on the interaction type. Add/remove interaction accordingly.
        $('#types').change(function(e) {
            featureType = $(this).find('option:selected').val();
            if (featureType == 'None') {
                $('#data').val('');
                clear_coords();
                map.removeInteraction(draw);
                vector_layer.getSource().clear();
                shpLayer.getSource().clear();
            } else if (featureType == 'Point') {
                clear_coords();
                shpLayer.getSource().clear();
                addInteraction(featureType);
            } else if (featureType == 'Polygon') {
                clear_coords();
                shpLayer.getSource().clear();
                addInteraction(featureType);
            } else if (featureType == 'Upload') {
                clear_coords();
                vector_layer.getSource().clear();
                shpLayer.getSource().clear();
                map.removeInteraction(draw);
                $modalUpload.modal('show');
            }
        }).change();
        init_events();



    };

    init_jquery_var = function() {
        //$('#current-servers').empty();
        $modalAddHS = $('#modalAddHS');
        $modalAddSOAP = $('#modalAddSoap');
        $SoapVariable = $('#soap_variable');
        $modalDelete = $('#modalDelete');
        $modalHIS = $('#modalHISCentral');
        $modalDataRods = $('#modalDataRods');
        $modalInterface = $('#modalInterface');
        $hs_list = $('#current-servers-list');
        $modalClimate = $('#modalClimate');
        $modalUpload = $("#modalUpload");
        $btnUpload = $("#btn-add-shp");

    };

    // $(function(){
    //     $('#cs_data_type').change(function () {
    //         //     var option = $(this).find('option:selected').val();
    //         // if(option == '6|Seasonal Forecast'){
    //         //     $modalClimate.append('<b>Bunch of random stuff</b>');
    //         //     $("#cs_forecast_variable").removeClass('hidden');
    //         // }else{
    //         //     $("#cs_forecast_variable").addClass('hidden');
    //         // }
    //
    //         var option = $(this).find('option:selected').val() != '6|Seasonal Forecast' ?  $("#cs_forecast_variable").addClass('hidden') : $('#cs_forecast_variable').show();
    //         // $('#cs_forecast_variable')[ ($(this).find('option:selected').val()=='6|Seasonal Forecast')? "hide" : "show" ]();
    //     });
    // });

    $(function() {

        //Change the Climate Serv Modal Form if Seasonal Forecast is selected
        $('#cs_data_type').change(function() {
            var selected_option = $(this).find('option:selected').val();
            $('#seasonal_forecast_start')[(selected_option == '6|Seasonal Forecast') ? "show" : "hide"]();
            $('#seasonal_forecast_end')[(selected_option == '6|Seasonal Forecast') ? "show" : "hide"]();
            $('#forecast_start')[(selected_option == '6|Seasonal Forecast') ? "hide" : "show"]();
            $('#forecast_end')[(selected_option == '6|Seasonal Forecast') ? "hide" : "show"]();
            $('#forecast')[(selected_option == '6|Seasonal Forecast') ? "show" : "hide"]();
            $('#ensemble')[(selected_option == '6|Seasonal Forecast') ? "show" : "hide"]();
            if (selected_option == '6|Seasonal Forecast') {
                $('label[for="forecast_start"]').hide();
                $('label[for="forecast_end"]').hide();
                $('label[for="seasonal_forecast_start"]').show();
                $('label[for="seasonal_forecast_end"]').show();
            } else {
                $('label[for="forecast_start"]').show();
                $('label[for="forecast_end"]').show();
                $('label[for="seasonal_forecast_start"]').hide();
                $('label[for="seasonal_forecast_end"]').hide();
            }


        }).change();
    });





    $(".settings").click(function() {
        $modalInterface.find('.success').html('');
    });

    //Get a list of current HydroServers in the CUAHSI HIS central
    get_his_server = function() {
        var datastring = $modalHIS.serialize();
        $.ajax({
            type: "POST",
            url: `${apiServer}/his-server/`,
            data: datastring,
            dataType: 'HTML',
            success: function(result) {
                var json_response = JSON.parse(result);
                var url = json_response.url;
                $('#soap-url').val(url);
                $('#modalHISCentral').modal('hide');

                $('#modalHISCentral').each(function() {
                    this.reset();
                });
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                console.log(Error);
            }
        });
    };
    $("#add-from-his").on('click', get_his_server);

    //Load the data rods page as modal
    get_data_rods = function() {
        if (($("#gldas-lat-lon").val() == "")) {
            $modalDataRods.find('.warning').html('<b>Please select a point on the map.</b>');
            return false;
        }
        if (($("#gldas-lat-lon").val() != "")) {
            $modalDataRods.find('.warning').html('');
        }
        $('#modalDataRods').modal('hide');

        var datastring = $modalDataRods.serialize();
        var details_url = `${apiServer}/datarods/?${datastring}`; //Sending the datarods modal information via the url

        var $loading = $('#view-gldas-loading');
        $('#gldas-container').addClass('hidden');
        $loading.removeClass('hidden');

        $('#gldas-container')
            .empty()
            .append('<iframe id="gldas-viewer" src="' + details_url + '" allowfullscreen></iframe>');
        $('#modalViewRods').modal('show');
        $('#gldas-viewer').one('load', function() {
            $loading.addClass('hidden');
            $('#gldas-container').removeClass('hidden');
            $loading.addClass('hidden');
        });

    };
    $("#get-data-rods").on('click', get_data_rods);

    //Loading the climate serv main page as a modal
    get_climate_serv = function() {
        // if (($("#cserv-lat-lon").val()=="")){
        //     $modalDataRods.find('.warning').html('<b>Please select a point on the map.</b>');
        //     return false;
        // }
        // if (($("#cserv-lat-lon").val()!= "")){
        //     $modalDataRods.find('.warning').html('');
        // }
        var datastring = $modalClimate.serialize();
        $('#modalClimate').modal('hide');
        //Sending the climate serv data via the url
        var details_url = `${apiServer}/cserv/?${datastring}`;
        // var data_type = $("#cs_data_type").val();
        // var operation_type = $("#cs_operation_type").val();
        // operation_type = operation_type.split("|");
        // var operation_int = operation_type[0];
        // var operation_var = operation_type[1];
        // var interval_type = $("#cs_interval_type").val();
        // var forecast_start = $("#forecast_start").val();
        // var forecast_end = $("#forecast_end").val();
        // var cserv_lat_lon = $("#cserv_lat_lon").val();
        //
        // var new_url = "cserv/?data_type="+data_type+"&operation_type_int="+operation_int+"&forecast_start="+forecast_start+"&forecast_end="+forecast_end+"&cserv_lat_lot="+cserv_lat_lon+"&operation_type_var="+operation_var+"&interval_type="+interval_type;
        // console.log(new_url);
        var $loading = $('#view-cserv-loading');
        $('#cserv-container').addClass('hidden');
        $loading.removeClass('hidden');

        $('#cserv-container').empty().append('<iframe id="cserv-viewer" src="' + details_url + '" allowfullscreen></iframe>');
        $('#modalViewCS').modal('show');
        $('#cserv-viewer').one('load', function() {
            $loading.addClass('hidden');
            $('#cserv-container').removeClass('hidden');
            $loading.addClass('hidden');
        });




    };
    $('#get-climate-serv').on('click', get_climate_serv);

    //Get a list of current HydroServers in the local database
    get_hs_list = function() {
        $.ajax({
            type: "GET",
            url: `${apiServer}/catalog/`,
            dataType: 'JSON',
            success: function(result) {
                //Dynamically generate the list of existing hydroservers
                var server = result['hydroserver'];
                var HSTableHtml = '<table id="tbl-hydroservers"><thead><th></th><th>Title</th><th>URL</th></thead><tbody>';
                if (server.length === 0) {
                    $modalDelete.find('.modal-body').html('<b>There are no hydroservers in the Catalog.</b>');
                } else {
                    for (var i = 0; i < server.length; i++) {
                        var title = server[i].title;
                        var url = server[i].url;
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
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                console.log(Error);
            }

        });
    };
    $("#delete-server").on('click', get_hs_list);

    //Load all the existing layers from the database
    load_catalog = () => {
        $.ajax({
            type: "GET",
            url: `${apiServer}/catalog/`,
            dataType: 'JSON',
            success: (result) => {

                var servers = result['hydroserver'];
                $('#current-servers').empty(); //Resetting the catalog
                servers.forEach(function(server) {
                    let {
                        title,
                        url,
                        geoserver_url,
                        layer_name,
                        extents
                    } = server;

                    let newHtml = `<li class="ui-state-default" layer-name="${title}">
                    <input class="chkbx-layer" type="checkbox" checked><span class="server-name">${title}</span>
                    <div class="hmbrgr-div"><img src="${staticPath}/images/hamburger.svg"></div>
                    </li>`;

                    let sld_string = `<StyledLayerDescriptor version="1.0.0">
                        <NamedLayer>
                            <Name>${layer_name}</Name>
                            <UserStyle>
                                <FeatureTypeStyle>
                                    <Rule>
                                        <PointSymbolizer>
                                            <Graphic>
                                                <Mark>
                                                    <WellKnownName>circle</WellKnownName>
                                                    <Fill>
                                                        <CssParameter name="fill">${set_color()}</CssParameter>
                                                    </Fill>
                                                </Mark>
                                                <Size>10</Size>
                                            </Graphic>
                                        </PointSymbolizer>
                                    </Rule>
                                </FeatureTypeStyle>
                            </UserStyle>
                        </NamedLayer>
                    </StyledLayerDescriptor>`;

                    $(newHtml).appendTo('#current-servers');
                    addContextMenuToListItem($('#current-servers').find('li:last-child'));

                    wmsSource = new ol.source.TileWMS({
                        url: geoserver_url,
                        params: {
                            'LAYERS': layer_name,
                            'SLD_BODY': sld_string
                        },
                        serverType: 'geoserver',
                        crossOrigin: 'Anonymous'
                    });

                    let projectedExtents = ol.proj.transformExtent([
                        parseFloat(extents.minx),
                        parseFloat(extents.miny),
                        parseFloat(extents.maxx),
                        parseFloat(extents.maxy)
                    ], 'EPSG:4326', 'EPSG:3857');


                    wmsLayer = new ol.layer.Tile({
                        extent: projectedExtents,
                        source: wmsSource
                    });

                    map.addLayer(wmsLayer);
                    layersDict[title] = wmsLayer;

                });

                var layer_extent = [-15478192.4796, -8159805.6435, 15497760.3589, 8159805.6435];
                map.getView().fit(layer_extent, map.getSize());
                map.updateSize();

            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                console.log(Error);
            }

        });


    };

    //Deleting a layer from the database and then deleting it from the frontend
    update_catalog = function() {
        $modalInterface.find('.success').html('');
        var datastring = $modalDelete.serialize(); //Delete the record in the database
        $.ajax({
            type: "POST",
            url: `${apiServer}/delete/`,
            data: datastring,
            dataType: 'HTML',
            success: function(result) {
                var json_response = JSON.parse(result);
                var title = json_response.title;
                $('#current-servers').empty(); //Resetting the catalog. So that it is updated.

                $('#modalDelete').modal('hide');
                $('#modalDelete').each(function() {
                    this.reset();
                });


                //Removing layer from the frontend
                map.removeLayer(layersDict[title]);
                delete layersDict[title];
                map.updateSize();
                load_catalog(); //Reloading the new catalog
                // click_catalog();
                $modalInterface.find('.success').html('<b>Successfully Updated the Catalog!</b>');
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                console.log(Error);
            }

        });

    };
    $("#btn-del-server").on('click', update_catalog);

    //Adding a REST endpoint. Obsolete for now. Can be put enabled to allow REST layers.
    add_server = function() {
        var datastring = $modalAddHS.serialize();
        if (($("#hs-title").val()) == "") {
            $modalAddSOAP.find('.warning').html('<b>Please enter a title. This field cannot be blank.</b>');
            return false;
        } else {
            $modalAddSOAP.find('.warning').html('');
        }
        if (($("#hs-url").val()) == "") {
            $modalAddSOAP.find('.warning').html('<b>Please enter a valid URL. This field cannot be blank.</b>');
            return false;
        } else {
            $modalAddSOAP.find('.warning').html('');
        }
        if (($("#hs-title").val()) != "") {
            var regex = new RegExp("^[a-zA-Z ]+$");
            var title = $("#soap-title").val();
            if (!regex.test(title)) {
                $modalAddSOAP.find('.warning').html('<b>Please enter Letters only for the title.</b>');
                return false;
            }
        } else {
            $modalAddSOAP.find('.warning').html('');
        }

        $.ajax({
            type: "POST",
            url: `${apiServer}/add-server/`,
            dataType: 'HTML',
            data: datastring,
            success: function(result) {
                var json_response = JSON.parse(result);
                if (json_response.status === 'true') {

                    let {
                        title,
                        wms: wms_url,
                        bounds: extents,
                        rest_url
                    } = json_response;

                    let newHtml = `<li class="ui-state-default" layer-name="${title}">
                    <input class="chkbx-layer" type="checkbox" checked><span class="server-name">${title}</span>
                    <div class="hmbrgr-div"><img src="${staticPath}/images/hamburger.svg"></div>
                    </li>`;


                    $(newHtml).appendTo('#current-servers');

                    addContextMenuToListItem($('#current-servers').find('li:last-child'));

                    $('#modalAddHS').modal('hide');

                    //map.addLayer(new_layer);
                    $('#modalAddHS').each(function() {
                        this.reset();
                    });
                    var sld_string = '<StyledLayerDescriptor version="1.0.0"><NamedLayer><Name>' + wms_url + '</Name><UserStyle><FeatureTypeStyle><Rule><PointSymbolizer><Graphic><Mark><WellKnownName>circle</WellKnownName><Fill><CssParameter name="fill">' + set_color() + '</CssParameter></Fill></Mark><Size>10</Size></Graphic></PointSymbolizer></Rule></FeatureTypeStyle></UserStyle></NamedLayer></StyledLayerDescriptor>';
                    wmsSource = new ol.source.TileWMS({
                        url: rest_url,
                        params: {
                            'LAYERS': wms_url,
                            'SLD_BODY': sld_string
                        },
                        serverType: 'geoserver',
                        crossOrigin: 'Anonymous'
                    });
                    wmsLayer = new ol.layer.Tile({
                        extent: ol.proj.transformExtent([extents['minx'], extents['miny'], extents['maxx'], extents['maxy']], 'EPSG:4326', 'EPSG:3857'),
                        source: wmsSource
                    });

                    map.addLayer(wmsLayer);

                    layersDict[title] = wmsLayer;

                    var layer_extent = wmsLayer.getExtent();
                    map.getView().fit(layer_extent, map.getSize());
                } else {
                    alert("Please Check your URL and Try Again.");
                }

            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                console.log(Error);
            }
        });

    };

    $('#btn-add-server').on('click', add_server);

    //Adding the SOAP endpoint layer to the map
    add_soap = function() {
        $modalInterface.find('.success').html('');
        //Validations to make sure that there are no issues with the form data
        if (($("#extent")).is(':checked')) {
            var zoom = map.getView().getZoom();
            if (zoom < 8) {
                $modalAddSOAP.find('.warning').html('<b>The zoom level has to be 8 or greater. Please check and try again.</b>');
                return false;
            } else {
                $modalAddSOAP.find('.warning').html('');
            }
            $("#chk_val").empty();
            var level = map.getView().calculateExtent(map.getSize());
            $('<input type="text" name="extent_val" id="extent_val" value=' + '"' + level + '"' + ' hidden>').appendTo($("#chk_val"));
            // $(this).val(level);
        }
        if (($("#soap-title").val()) == "") {
            $modalAddSOAP.find('.warning').html('<b>Please enter a title. This field cannot be blank.</b>');
            return false;
        } else {
            $modalAddSOAP.find('.warning').html('');
        }
        if (($("#soap-url").val()) == "") {
            $modalAddSOAP.find('.warning').html('<b>Please enter a valid URL. This field cannot be blank.</b>');
            return false;
        } else {
            $modalAddSOAP.find('.warning').html('');
        }
        if (($("#soap-url").val()) == "http://hydroportal.cuahsi.org/nwisdv/cuahsi_1_1.asmx?WSDL" || ($("#soap-url").val()) == "http://hydroportal.cuahsi.org/nwisuv/cuahsi_1_1.asmx?WSDL") {
            $modalAddSOAP.find('.warning').html('<b>Please zoom in further to be able to access the NWIS Values</b>');
            return false;
        } else {
            $modalAddSOAP.find('.warning').html('');
        }
        if (($("#soap-title").val()) != "") {
            var regex = new RegExp("^[a-zA-Z ]+$");
            var title = $("#soap-title").val();
            if (!regex.test(title)) {
                $modalAddSOAP.find('.warning').html('<b>Please enter Letters only for the title.</b>');
                return false;
            }
        } else {
            $modalAddSOAP.find('.warning').html('');
        }
        var datastring = $modalAddSOAP.serialize();

        //Submitting the data to the controller
        $.ajax({
            type: "POST",
            url: `${apiServer}/soap/`,
            dataType: 'HTML',
            data: datastring,
            success: function(result) {
                //Returning the geoserver layer metadata from the controller
                var json_response = JSON.parse(result);
                if (json_response.status === 'true') {

                    var title = json_response.title;
                    var wms_url = json_response.wms;
                    var extents = json_response.bounds;
                    var rest_url = json_response.rest_url;
                    var zoom = json_response.zoom;
                    if (zoom == 'true') {
                        var level = json_response.level;
                    }

                    let newHtml = `<li class="ui-state-default" layer-name="${title}">
                    <input class="chkbx-layer" type="checkbox" checked><span class="server-name">${title}</span>
                    <div class="hmbrgr-div"><img src="${staticPath}/images/hamburger.svg"></div>
                    </li>`;

                    $(newHtml).appendTo('#current-servers');

                    addContextMenuToListItem($('#current-servers').find('li:last-child')); //Adding the element to the Current HydroServers box

                    $('#modalAddSoap').modal('hide');

                    //map.addLayer(new_layer);
                    $('#modalAddSoap').each(function() {
                        this.reset();
                    });

                    //Stlying string to manage the styling of the points on the layer
                    var sld_string = '<StyledLayerDescriptor version="1.0.0"><NamedLayer><Name>' + wms_url + '</Name><UserStyle><FeatureTypeStyle><Rule><PointSymbolizer><Graphic><Mark><WellKnownName>circle</WellKnownName><Fill><CssParameter name="fill">' + set_color() + '</CssParameter></Fill></Mark><Size>10</Size></Graphic></PointSymbolizer></Rule></FeatureTypeStyle></UserStyle></NamedLayer></StyledLayerDescriptor>';

                    //Adding the wms layer to the gloval source/layer
                    wmsSource = new ol.source.TileWMS({
                        url: rest_url,
                        params: {
                            'LAYERS': wms_url,
                            'SLD_BODY': sld_string
                        },
                        serverType: 'geoserver',
                        crossOrigin: 'Anonymous'
                    });
                    wmsLayer = new ol.layer.Tile({
                        extent: ol.proj.transformExtent([extents['minx'], extents['miny'], extents['maxx'], extents['maxy']], 'EPSG:4326', 'EPSG:3857'),
                        source: wmsSource
                    });

                    map.addLayer(wmsLayer);

                    //Adding the layer to the global layers dict to keep track of layers
                    layersDict[title] = wmsLayer;

                    var layer_extent = wmsLayer.getExtent();
                    map.getView().fit(layer_extent, map.getSize());
                    $modalInterface.find('.success').html('<b>Successfully Added the HydroServer to the Map!</b>');
                } else {
                    $modalAddSOAP.find('.warning').html('<b>Failed to add server. Please check Url and try again.</b>');
                }

            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                //Error handling
                $modalAddSOAP.find('.warning').html('<b>Invalid Hydroserver SOAP Url. Please check and try again.</b>');
                if (($("#extent")).is(':checked')) {
                    $modalAddSOAP.find('.warning').html('<b>The requested area does not have any sites. Please try another area.</b>');
                    return false;
                } else {
                    $modalAddSOAP.find('.warning').html('');
                }

            }
        });

    };
    $('#btn-add-soap').on('click', add_soap);


    //Reverse coding to find the name of the clicked location
    location_search = function() {
        function geocoder_success(results, status) {
            if (status == google.maps.GeocoderStatus.OK) {
                var r = results;
                var flag_geocoded = true;
                var Lat = results[0].geometry.location.lat();
                var Lon = results[0].geometry.location.lng();
                var dbPoint = {
                    "type": "Point",
                    "coordinates": [Lon, Lat]
                };

                var coords = ol.proj.transform(dbPoint.coordinates, 'EPSG:4326', 'EPSG:3857');
                map.getView().setCenter(coords);
                map.getView().setZoom(12);
            } else {
                alert("Geocode was not successful for the following reason: " + status);
            }
        }
        var g = new google.maps.Geocoder();
        var search_location = document.getElementById('location_input').value;
        g.geocode({ 'address': search_location }, geocoder_success);

    };
    $('#location_search').on('click', location_search);

    //On click zoom to the relevant layer
    onClickZoomTo = function(e) {
        var clickedElement = e.trigger.context;
        var $lyrListItem = $(clickedElement).parent().parent();
        var layer_name = $lyrListItem.attr('layer-name');
        var layer_extent = layersDict[layer_name].getExtent();
        map.getView().fit(layer_extent, map.getSize());
        map.updateSize();
    };

    //On click delete the layer, but it won't delete it from the database
    onClickDeleteLayer = function(e) {
        var clickedElement = e.trigger.context;
        var $lyrListItem = $(clickedElement).parent().parent();
        var layer_name = $lyrListItem.attr('layer-name');
        map.removeLayer(layersDict[layer_name]);
        delete layersDict[layer_name];
        $lyrListItem.remove();
        map.updateSize();
    };

    init_events = function() {
        (function() {
            var target, observer, config;
            // select the target node
            target = $('#app-content-wrapper')[0];

            observer = new MutationObserver(function() {
                window.setTimeout(function() {
                    map.updateSize();
                }, 350);
            });
            $(window).on('resize', function() {
                map.updateSize();
            });

            config = { attributes: true };

            observer.observe(target, config);
        }());

        //Toggle the layer on and off on click
        $(document).on('change', '.chkbx-layer', function() {
            var displayName = $(this).next().text();
            layersDict[displayName].setVisible($(this).is(':checked'));
        });

        // $(document).ajaxStart($.blockUI).ajaxStop($.unblockUI);

        //Map on zoom function. To keep track of the zoom level. Certain HydroServers can only be added at a certain zoom level.
        map.on("moveend", function() {
            var zoom = map.getView().getZoom();
            var zoomInfo = '<h6>Current Zoom level = ' + zoom + '</h6>';
            document.getElementById('zoomlevel').innerHTML = zoomInfo;
            // Object.keys(layersDict).forEach(function(key){
            //     var source =  layersDict[key].getSource();
            // });
        });

        map.on("singleclick", function(evt) {

            $(element).popover('destroy');


            if (map.getTargetElement().style.cursor == "pointer" && $('#types').val() == 'None') {
                var clickCoord = evt.coordinate; //Get the coordinate of the clicked point
                popup.setPosition(clickCoord);
                // map.getLayers().item(1).getSource().clear();

                var view = map.getView();
                var viewResolution = view.getResolution();


                var wms_url = current_layer.getSource().getGetFeatureInfoUrl(evt.coordinate, viewResolution, view.getProjection(), { 'INFO_FORMAT': 'application/json' }); //Get the wms url for the clicked point
                if (wms_url) {
                    //Retrieving the details for clicked point via the url
                    $.ajax({
                        type: "GET",
                        url: wms_url,
                        dataType: 'json',
                        success: function(result) {

                            var site_name = result["features"][0]["properties"]["sitename"];
                            var site_code = result["features"][0]["properties"]["sitecode"];
                            var network = result["features"][0]["properties"]["network"];
                            var hs_url = result["features"][0]["properties"]["url"];
                            var service = result["features"][0]["properties"]["service"];
                            var details_html = `${apiServer}/details/?sitename=${site_name}&sitecode=${site_code}&network=${network}&hsurl=${hs_url}&service=${service}&hidenav=true`; //passing the information through the url

                            $(element).popover({
                                'placement': 'top',
                                'html': true,
                                //Dynamically Generating the popup content
                                'content': '<table border="1"><tbody><tr><th>Site Name</th><th>Site Id</th><th>Details</th></tr>' + '<tr><td>' + site_name + '</td><td>' + site_code + '</td><td><button type="button" class="mod_link btn-primary" data-html="' + details_html + '" >Site Details</button></td></tr>'
                            });

                            $(element).popover('show');
                            $(element).next().css('cursor', 'text');
                            //Showing the details page when clicking on site details
                            $('.mod_link').on('click', function() {
                                var $loading = $('#view-file-loading');
                                $('#iframe-container').addClass('hidden');
                                $loading.removeClass('hidden');
                                var details_url = $(this).data('html');
                                $('#iframe-container')
                                    .empty()
                                    .append('<iframe id="iframe-details-viewer" src="' + details_url + '" allowfullscreen></iframe>');
                                $('#modalViewDetails').modal('show');
                                $('#iframe-details-viewer').one('load', function() {
                                    $loading.addClass('hidden');
                                    $('#iframe-container').removeClass('hidden');
                                    $loading.addClass('hidden');
                                });
                            });
                        },
                        error: function(XMLHttpRequest, textStatus, errorThrown) {
                            console.log(Error);
                        }
                    });
                }
            }



        });

        $('#close-modalViewDetails').on('click', function() {
            $('#modalViewDetails').modal('hide');
        });
        $('#close-modalViewRods').on('click', function() {
            $('#modalViewRods').modal('hide');
        });
        $('#close-modalClimateServ').on('click', function() {
            $('#modalClimateServ').modal('hide');
        });
        $('#close-modalViewCS').on('click', function() {
            $('#modalViewCS').modal('hide');
        });

        //Only show the pointer for layers that aren't base layer, shapefile layer and the point/polygon feature layer
        map.on('pointermove', function(evt) {
            if (evt.dragging) {
                return;
            }
            var pixel = map.getEventPixel(evt.originalEvent);
            var hit = map.forEachLayerAtPixel(pixel, function(layer) {
                if (layer != layers[0] && layer != layers[1] && layer != layers[2]) {
                    current_layer = layer;
                    return true;
                }
            });
            map.getTargetElement().style.cursor = hit ? 'pointer' : '';
        });


    };

    //Initialize the context menu (The little hamburger in the Current HydroServers list item). It currently supports zoom to or delete layer. You can add more functionality here.
    init_menu = function() {
        ContextMenuBase = [{
                name: 'Zoom To',
                title: 'Zoom To',
                fun: function(e) {
                    onClickZoomTo(e);
                }
            },
            {
                name: 'Delete',
                title: 'Delete',
                fun: function(e) {
                    onClickDeleteLayer(e);
                }
            }
        ];
    };

    //Generate a graph based on the REST endpoint request. Somewhat obsolete now, but leaving it here in case you want to allow REST endpoints in the future.
    generate_graph = function() {
        $(document).find('.warning').html('');
        var variable = $('#select_var option:selected').val();

        $.ajax({
            type: "GET",
            url: `${apiServer}/rest-api/`,
            dataType: 'JSON',
            success: function(result) {

                for (var i = 0; i < result['graph'].length; i++) {
                    if (result['graph'][i]['variable'] == variable) {
                        $('#container').highcharts({
                            chart: {
                                type: 'area',
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
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                $(document).find('.warning').html('<b>Unable to generate graph. Please check the start and end dates and try again.</b>');
                console.log(Error);
            }
        });

    };

    $('#generate-graph').on('click', generate_graph);

    //Generate the time series plot of SOAP request
    generate_plot = function() {
        var $loading = $('#view-file-loading');
        $loading.removeClass('hidden');
        $("#plotter").addClass('hidden');
        var datastring = $SoapVariable.serialize(); //Can change this approach by adopting the workflow used in the upload_shp function
        $.ajax({
            type: "POST",
            url: `${apiServer}/soap-api/`,
            dataType: 'JSON',
            data: datastring,
            success: function(result) {
                //Using Highcharts JavaScript Code to create a time series plot
                //Using the json response to render the chart as needed

                let vals = result['values'].filter((val) => {
                    return val[1] != -9999 && val[1] != "-9999"
                });

                $('#plotter').highcharts({
                    chart: {
                        type: 'area',
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
                        enabled: true
                    },
                    series: [{
                        data: vals,
                        name: result['variable']
                    }]

                });
                $("#plotter").removeClass('hidden');
                $loading.addClass('hidden');

            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                $(document).find('.warning').html('<b>Unable to generate graph. Please check the start and end dates and try again.</b>');
                console.log(Error);
            }
        });
        return false;

    };

    $('#generate-plot').on('click', generate_plot);

    //Adding the context menu capability to a list item aka the recently added HydroServer layer
    addContextMenuToListItem = function($listItem) {
        var contextMenuId;

        $listItem.find('.hmbrgr-div img')
            .contextMenu('menu', ContextMenuBase, {
                'triggerOn': 'click',
                'displayAround': 'trigger',
                'mouseClick': 'left',
                'position': 'right',
                'onOpen': function(e) {
                    $('.hmbrgr-div').removeClass('hmbrgr-open');
                    $(e.trigger.context).parent().addClass('hmbrgr-open');
                },
                'onClose': function(e) {
                    $(e.trigger.context).parent().removeClass('hmbrgr-open');
                }
            });
        contextMenuId = $('.iw-contextMenu:last-child').attr('id');
        $listItem.attr('data-context-menu', contextMenuId);
    };

    //This clicks on each element in the Current HydroServers box. This was experimental.
    click_catalog = function() {
        $('.iw-contextMenu').find('[title="Zoom To"]').each(function(index, obj) {
            obj.click();
        });
        map.updateSize();
    };

    createExportCanvas = function(mapCanvas) {

        var exportCanvas;
        var context;


        exportCanvas = $('#export-canvas')[0];
        exportCanvas.width = mapCanvas.width;
        exportCanvas.height = mapCanvas.height;
        context = exportCanvas.getContext('2d');
        context.drawImage(mapCanvas, 0, 0);
        return exportCanvas;

    };

    //The following is hidden for now. But in the future can be used to generate an alert with the screenshot of the map
    $('#gen-alert').on('click', function() {
        var dims = {
            a0: [1189, 841],
            a1: [841, 594],
            a2: [594, 420],
            a3: [420, 297],
            a4: [297, 210],
            a5: [210, 148]
        };

        var dim = dims['a4'];

        map.once('postcompose', function(event) {
            var canvas = createExportCanvas(event.context.canvas);
            var pdf = new jsPDF('potrait', undefined, 'a4');
            var data = canvas.toDataURL('image/png');
            var app_logo = "data:image/jpeg;base64";
            pdf.setFontSize(25);
            pdf.setTextColor(255, 0, 0);
            pdf.text(75, 15, "FLOOD ALERT");
            pdf.addImage(app_logo, 'JPEG', 165, 150, 15, 15);
            pdf.addImage(icimod_logo, 'JPEG', 5, 3, 15, 15);
            pdf.addImage(data, 'JPEG', 25, 20, 160, 120);
            // var cur_date = new Date();
            // var rand_str = btoa(pdf.output('datauristring'));
            // console.log(rand_str);
            // var pdf_name = cur_date.toString()+'.pdf';
            pdf.save('FloodAlert.pdf');
        });
        map.renderSync();
    });

    upload_file = function() {
        //Preparing the data to be sent as an ajax request
        var files = $("#shp-upload-input")[0].files;
        var data;
        $modalUpload.modal('hide');
        $("#modalMapConsole").modal('hide');
        data = prepare_files(files);
        $.ajax({
            url: `${apiServer}/upload-shp/`,
            type: 'POST',
            data: data,
            dataType: 'json',
            processData: false,
            contentType: false,
            error: function(status) {

            },
            success: function(response) {
                var extents = response.bounds;
                shpSource = new ol.source.Vector({
                    features: (new ol.format.GeoJSON()).readFeatures(response.geo_json) //Reading the geojson object
                });
                shpLayer = new ol.layer.Vector({
                    name: 'shp_layer',
                    extent: [extents[0], extents[1], extents[2], extents[3]], //Note: If you don't define the extents, you cannot get OpenLayers to zoom to it. It just doesn't do it.
                    source: shpSource,
                    style: new ol.style.Style({ //Change the following to change the styling of the shapefile object
                        stroke: new ol.style.Stroke({ //This defines the boundary
                            color: 'blue',
                            lineDash: [4],
                            width: 3
                        }),
                        fill: new ol.style.Fill({
                            color: 'rgba(0, 0, 255, 0.1)' //The 0.1 refers to opacity
                        })
                    })
                });
                map.addLayer(shpLayer);


                map.getView().fit(shpLayer.getExtent(), map.getSize()); //Zoom to the map after adding the geojson object
                map.updateSize();
                map.render();

                //Creating geojson string so that it can be passed through the cserv-lat-lon hidden field
                //Reprojecting the coordinates
                var min = ol.proj.transform([extents[0], extents[1]], 'EPSG:3857', 'EPSG:4326');
                var max = ol.proj.transform([extents[2], extents[3]], 'EPSG:3857', 'EPSG:4326');
                var min2 = ol.proj.transform([extents[0], extents[3]], 'EPSG:3857', 'EPSG:4326');
                var max2 = ol.proj.transform([extents[2], extents[1]], 'EPSG:3857', 'EPSG:4326');
                var coord_list = ['[' + min + ']', '[' + max2 + ']', '[' + max + ']', '[' + min2 + ']', '[' + min + ']']; //Creating a list of coordinates
                var json_str = '{"type":"Polygon","coordinates":[[' + coord_list + ']]}'; //Creating the json string

                $("#cserv_lat_lon").val(json_str); //Setting the json string as the value of the cserv-lat-lon
                $modalClimate.modal('show');

            }
        });
    };

    $("#btn-add-shp").on('click', upload_file);

    //Preparing files so that they can be submitted via an ajax request
    prepare_files = function(files) {
        var data = new FormData();

        Object.keys(files).forEach(function(file) {
            data.append('files', files[file]);
        });

        return data;
    };

    //The following three functions are necessary to make dynamic ajax requests
    addDefaultBehaviorToAjax = function() {
        // Add CSRF token to appropriate ajax requests
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!checkCsrfSafe(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
                }
            }
        });
    };

    checkCsrfSafe = function(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    };

    getCookie = function(name) {
        var cookie;
        var cookies;
        var cookieValue = null;
        var i;

        if (document.cookie && document.cookie !== '') {
            cookies = document.cookie.split(';');
            for (i = 0; i < cookies.length; i += 1) {
                cookie = $.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    /************************************************************************
     *                  INITIALIZATION / CONSTRUCTOR
     *************************************************************************/
    $(function() {

        init_jquery_var();
        addDefaultBehaviorToAjax();
        init_menu();
        init_map();
        load_catalog();

    });

}()); // End of package wrapper