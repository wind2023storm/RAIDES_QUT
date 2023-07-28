$(document).ready(function () {

    // Updates the Results and other tabs row count being displayed
    function updateTableHeaders() {
        // EPM tabs
        $("#nav-epm-grant-tab span").text(`${$("#epm-grant-table").DataTable().rows().count()}`);
        $("#nav-epm-applications-tab span").text(`${$("#epm-applications-table").DataTable().rows().count()}`);

        // MDL tabs
        $("#nav-mdl-grant-tab span").text(`${$("#mdl-grant-table").DataTable().rows().count()}`);
        $("#nav-mdl-applications-tab span").text(`${$("#mdl-applications-table").DataTable().rows().count()}`);
        
        // ML tabs
        $("#nav-ml-grant-tab span").text(`${$("#ml-grant-table").DataTable().rows().count()}`);
        $("#nav-ml-applications-tab span").text(`${$("#ml-applications-table").DataTable().rows().count()}`);

        // EPC tabs
        $("#nav-epc-grant-tab span").text(`${$("#epc-grant-table").DataTable().rows().count()}`);
        $("#nav-epc-applications-tab span").text(`${$("#epc-applications-table").DataTable().rows().count()}`);

        // Cadastre tab
        $("#nav-cadastre-tab span").text(`${$("#cadastre-table").DataTable().rows().count()}`);

        // Display Table Panel Title with total result count
        $("#map-footer").empty();
        $("#map-footer").append(`Results <span class="badge rounded-pill">
                    ${$("#epm-grant-table").DataTable().rows().count() + $("#epm-applications-table").DataTable().rows().count() 
                    + $("#mdl-grant-table").DataTable().rows().count() +$("#mdl-applications-table").DataTable().rows().count() 
                    + $("#ml-grant-table").DataTable().rows().count() + $("#ml-applications-table").DataTable().rows().count() 
                    + $("#epc-grant-table").DataTable().rows().count() + $("#epc-applications-table").DataTable().rows().count() 
                    + $("#cadastre-table").DataTable().rows().count()}</span>`);  
    }

    // create table for each selection layers (tenements)
    function createTable(tableName, tableColumns){
        var newTable = $(tableName).DataTable({
            lengthMenu: [            // pagination count
                [10, 25, 50, -1],    // number
                [10, 25, 50, "All"], //display number
            ],
            columns: tableColumns,   // column headers
            columnDefs: [{           // Replace empty column value with None
                "defaultContent": "None",
                "targets": "_all"
            }],
            dom: 'Bfrt<"row"<"col-sm-12 col-md-3"l><"col-sm-12 col-md-4"i><"col-sm-12 col-md-5"p>>', // setting position table, search, toolbar and pagination
            buttons: [              // Buttons to display in toolbar
                {
                    text: '<i class="fa fa-trash"></i>',                                // delete button
                    action: function(){
                        $(tableName).DataTable().rows(".selected").remove().draw();
                        updateTableHeaders();
                    },
                },
                {
                    extend: 'colvis',
                    collectionLayout: 'fixed columns',
                    collectionTitle: 'Column Visibility Control'
                },   
                {
                    extend: 'columnToggle',
                    text: "Show/Hide All"
                },                                                            // column visibility toggle
                {
                    extend: "collection",                                               // export button
                    className: "custom-html-collection",
                    text: "Export",
                    buttons: [
                        'csv',                                                          // csv
                        'excel',                                                        // excel
                        {
                            text: "JSON",                                               // JSON
                            action: function (e, dt, button, config) {
                                var data = dt.buttons.exportData();
    
                                $.fn.dataTable.fileSave(
                                    new Blob([JSON.stringify(data)]),
                                    "Interactive Map.json"
                                );
                            },
                        },
                    ],
                },
            ],
            select: {                                                                    // Select multiple rows to delete
                style: "multi",
            },
        });
        return newTable;
    }

    // creates data displayed by the layer selected on the map
    function generateSelectionLayer(data, tooltipFields, tooltipAlias, layerColor=null){
        var selectionLayer = L.geoJson(data, {
            
            style: function (feature) {                                               // Polygon Colour
                if (layerColor === null){
                    return {color: feature.properties.COLOR};
                }
                else{
                    return {color: layerColor}
                }
            },
            
            onEachFeature: function onEachFeature(feature, layer) {
                layer.on({                                                          // Events on mouse hover and click
                    // Highlight Tenement when hovering over it
                    mouseover: function (tenement) {
                                    var layer = tenement.target;
                                    layer.setStyle({
                                        weight: 5,
                                        fillOpacity: 0.7
                                    });
                                    layer.bringToFront();
                                },
                    // UN-Highlight tenement when not hovering over it
                    mouseout: function (tenement) {
                                    selectionLayer.resetStyle(tenement.target);
                                },
                    // Zoom to Tenement when it is clicked
                    click: function (tenement) {
                                    map.fitBounds(tenement.target.getBounds());
                                },
                });

                layer.bindTooltip(function (layer) {                                // creating tooltip
                    let div = L.DomUtil.create('div');
                    let handleObject = feature => typeof (feature) == 'object' ? JSON.stringify(feature) : feature;
                    let fields = tooltipFields; //Geojson file data properties
                    let aliases = tooltipAlias; //Name to display above properties args
                    // Table to display in the popup
                    let table = '<table>' + String(fields.map((v, i) =>
                            `<tr>
								<th>${aliases[i]}</th>
								
								<td>${handleObject(layer.feature.properties[v])}</td>
							</tr>`).join(''))
                        + '</table>';
                    div.innerHTML = table;
                    return div
                }, {
                    sticky: true, // whether to follow the mouse or not
                    className: "map-tooltip" // display design class
                });
            }
        })
        return selectionLayer
    }

    // Generates dates based on the number of behind the current date
    function generateTimeRanges(timeRanges){
        let currentDate = new Date()
        let dateRange = []
        for( let i = 0; i < timeRanges.length; i++){
            currentDate.setDate(currentDate.getDate() - timeRanges[i])      // generates the next date
            dateRange.push(currentDate.toISOString().substring(0, 10))      // stores them as string
            }
        return dateRange
        }
    
    // generates colours for the epm layers based on their dates (except expiring)
    function getEPMColor(tenementDate, timeRanges, colors){
        for( let i = timeRanges.length - 1; i > -1; i--){                   // goes from the earliest to latest date
            if (tenementDate < timeRanges[i]){                              // checks if the date is earlier than the dates for the tenement
                return colors[i+1]                                          // assigns the color
            }
        }
        return colors[0]                                                    // in case the tenement recently got assigned to the layer
    }

    // creates Legends for the EPM layers (except expiring)
    function generateLegend(timeRanges, colors, legendTitle, legendPosition="bottomright"){
        let dateRanges = []                                                 // date ranges of the epm layer
        let displayLegends = []
        let currentDate = new Date().toISOString().substring(0, 10);
        dateRanges.push(timeRanges[0] + " - " + currentDate)                // latest range
        for(let i = 0; i < timeRanges.length - 1; i++){
            dateRanges.push(timeRanges[i+1] + " - " + timeRanges[i])        // every range in between
        }
        dateRanges.push("BEFORE " + timeRanges[timeRanges.length - 1])      // earliest range
        for(let i = dateRanges.length - 1; i > -1; i--){
            displayLegends.push(                                            // generating legends for each date range
                {
                    label: dateRanges[i],
                    type: "polygon",
                    sides: 4,
                    color: colors[i],
                    fillColor: colors[i],
                    fillOpacity: 0.3,
                    weight: 2
                })
        }   
        return L.control.Legend({                                           // generating leaflet legend and sending it back
                    position: legendPosition,
                    title: legendTitle,
                    legends: displayLegends
                });
    }

    // columns for grant MDL and ML tables
    var permitGrantColumns = [
        {title: "Permit Number", data: "DISPLAYNAM"},
        {title: "Permit Type", data: "PERMITTY_1"},
        {title: "Permit Status", data: "PERMITST_1"},
        {title: "Permit sub-status", data: "PERMITST_2"},
        {title: "Lodge Date", data: "LODGEDATE"},
        {title: "Grant Date", data: "APPROVEDAT"},
        {title: "Expiry Date", data: "EXPIRYDATE"},
        {title: "Authorised Holder Name", data: "AUTHORIS_1"},
        {title: "Native Title Category", data: "NATIVETITL"},
        {title: "Mineral", data: "PERMITMINE"},
        {title: "Purpose", data: "PERMITPURP"},
        {title: "Area(ha)", data: "SHAPEAREAH"},
        {title: "Permit Name", data: "PERMITNAME"},
        {title: "Permit Number Other", data: "PERMITNUMB"},
        {title: "Permit Type Abbreviation", data: "PERMITTY_2"},
        {title: "Permit ID", data: "PERMITID"},
    ]

    // columns for applicaiton MDL and ML tables
    var permitApplicationsColumns =  [
        {title: "Permit Number", data: "DISPLAYNAM"},
        {title: "Permit Type", data: "PERMITTY_1"},
        {title: "Permit Status", data: "PERMITST_1"},
        {title: "Permit sub-status", data: "PERMITST_2"},
        {title: "Lodge Date", data: "LODGEDATE"},
        {title: "Authorised Holder Name", data: "AUTHORIS_1"},
        {title: "Native Title Category", data: "NATIVETITL"},
        {title: "Mineral", data: "PERMITMINE"},
        {title: "Purpose", data: "PERMITPURP"},
        {title: "Area(ha)", data: "SHAPEAREAH"},
        {title: "Permit Name", data: "PERMITNAME"},
        {title: "Permit Number Other", data: "PERMITNUMB"},
        {title: "Permit Type Abbreviation", data: "PERMITTY_2"},
        {title: "Permit ID", data: "PERMITID"},
    ]

    // columns for EPM Grants
    var epmGrantColumns = [
        {title: "Permit Number", data: "DISPLAYNAM"},
        {title: "Permit Type", data: "PERMITTY_1"},
        {title: "Permit Status", data: "PERMITST_1"},
        {title: "Permit sub-status", data: "PERMITST_2"},
        {title: "Lodge Date", data: "LODGEDATE"},
        {title: "Grant Date", data: "APPROVEDAT"},
        {title: "Expiry Date", data: "EXPIRYDATE"},
        {title: "Authorised Holder Name", data: "AUTHORIS_1"},
        {title: "Native Title Category", data: "NATIVETITL"},
        {title: "Mineral", data: "PERMITMINE"},
        {title: "Purpose", data: "PERMITPURP"},
        {title: "Sub-Block Count", data: "AREA_SUBBL"},
        {title: "Permit Name", data: "PERMITNAME"},
        {title: "Permit Number Other", data: "PERMITNUMB"},
        {title: "Permit Type Abbreviation", data: "PERMITTY_2"},
        {title: "Permit ID", data: "PERMITID"},
        {title: "MDL", data: "MDL"},
        {title: "ML", data: "ML"},
        {title: "EPC", data: "EPC"},
        {title: "Lot / Plan Number", data: "CADASTRE"},
    ]

    // columns for EPM Applications
    var epmApplicationsColumns = [
        {title: "Permit Number", data: "DISPLAYNAM"},
        {title: "Permit Type", data: "PERMITTY_1"},
        {title: "Permit Status", data: "PERMITST_1"},
        {title: "Permit sub-status", data: "PERMITST_2"},
        {title: "Lodge Date", data: "LODGEDATE"},
        {title: "Authorised Holder Name", data: "AUTHORIS_1"},
        {title: "Native Title Category", data: "NATIVETITL"},
        {title: "Mineral", data: "PERMITMINE"},
        {title: "Purpose", data: "PERMITPURP"},
        {title: "Sub-Block Count", data: "AREA_SUBBL"},
        {title: "Permit Name", data: "PERMITNAME"},
        {title: "Permit Number Other", data: "PERMITNUMB"},
        {title: "Permit Type Abbreviation", data: "PERMITTY_2"},
        {title: "Permit ID", data: "PERMITID"},
        {title: "MDL", data: "MDL"},
        {title: "ML", data: "ML"},
        {title: "EPC", data: "EPC"},
        {title: "Lot / Plan Number", data: "CADASTRE"},
    ]
    
    // Generating Tables
    var epmGrantedTable = createTable("#epm-grant-table", epmGrantColumns)                      // EPM Grants
    var epmApplicationsTable = createTable("#epm-applications-table", epmApplicationsColumns)      // EPM Applicaitons
    var mdlGrantedTable = createTable("#mdl-grant-table", permitGrantColumns)                   // MDL Permit Grants
    var mdlApplicationsTable = createTable("#mdl-applications-table", permitApplicationsColumns)   // MDL Permit Applications
    var mlGrantedTable = createTable("#ml-grant-table", permitGrantColumns)                     // ML Permits Grants
    var mlApplicationsTable = createTable("#ml-applications-table", permitApplicationsColumns)     // ML Permit Applications
    var epcGrantedTable = createTable("#epc-grant-table", permitGrantColumns)                     // EPC Permits Grants
    var epcApplicationsTable = createTable("#epc-applications-table", permitApplicationsColumns)     // EPC Permit Applications
    var cadastreTable = createTable("#cadastre-table", [                                        // Cadastre
        {title: "LOT", data: "LOT"},
        {title: "PLAN", data: "PLAN"},
        {title: "ACC_CODE", data: "ACC_CODE"},
    ])

    // creating main map container with fullscreena and toolbar
    const map = L.map('map', {drawControl: true, fullscreenControl: true,}).setView([-20.917574, 142.702789], 6);

    //adding world map to map container
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    // creating mini map's world map
    const minitiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        minZoom: 2, maxZoom: 3,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    })
    // generating mini map
    new L.Control.MiniMap(minitiles, {toggleDisplay: true}).addTo(map);

    // Selection Layers
    var cadastreLayer = new L.FeatureGroup();                               // Cadastre
    var mdlApplicationsLayer = new L.featureGroup({});                      // MDL Permit Applications
    var mdlGrantedLayer = new L.featureGroup({});                           // MDL Permit Granted
    var mlApplicationsLayer = new L.featureGroup({});                       // ML Permit Applications
    var mlGrantedLayer = new L.featureGroup({});                            // ML Permit Granted
    var epcApplicationsLayer = new L.featureGroup({});                       // ML Permit Applications
    var epcGrantedLayer = new L.featureGroup({});                            // ML Permit Granted
    var epmMoratoriumLayer = new L.featureGroup({});                        // Moratorium
    var epmApplicationsLayer = new L.featureGroup({}).addTo(map);           // Pending Applications
    var epmGrantedLayer = new L.featureGroup({}).addTo(map);                // Granted Exploration Permits
    var epmExpiringLayer = new L.featureGroup({});                          // EPM Approaching Expiry
    
    // Non-Selection Layers
    var fillExpiringLayer = new L.featureGroup({}).addTo(epmExpiringLayer); // Refill Approaching expiry with tenements when removed
    var searchTenementFeature = new L.featureGroup({});                     // Stores all the selection layers to search through
    var toolbarLayer = new L.FeatureGroup().addTo(map);                     // Stores user drawn shapes

    // creating tenement search box
    var searchBox = new L.Control.Search({
        layer: searchTenementFeature,
        propertyName: 'DISPLAYNAM', // dataset property to search
        initial: false,
        marker: false,
        autoCollapse: true,
        textPlaceholder: 'Type Permit',
        // zoom to location
        moveToLocation: function (latlng) {
            map.fitBounds(latlng['layer']._bounds);
        },
    });

    // Zoom to tenement on finding tenement location
    searchBox.on('search_locationfound',
        function (tenement) {
            map.fitBounds(tenement.target.getBounds());
        });
    
    map.addControl(searchBox);

    // miles/km scale to display coordinates
    L.control.scale().addTo(map);

    // mouse coordinate tracker
    const Coordinates = L.Control.extend({
        onAdd: map => {
            const container = L.DomUtil.create("div");
            map.addEventListener("mousemove", tenement => {
                container.innerHTML = `
                      <p>Latitude: ${tenement.latlng.lat.toFixed(4)} | 
                        Longitude: ${tenement.latlng.lng.toFixed(4)}
                      </p>`;
            });
            return container;
        }
    });
    map.addControl(new Coordinates({position: "bottomleft"}));

    // generates time ranges and colours for each EPM layer (except expiring), the array has size of a range (in days)
    var morTimeRange = generateTimeRanges([7, 14, 14, 21])
    var morColors = ['#500043','#82006C', '#C800A7', '#FF73E8', '#FFCDF7']
    var appTimeRange = generateTimeRanges([365, 365, 365, 365])
    var appColors = ['#b40426', '#ee8468', '#9e7662', '#7b9ff9', '#3b4cc0']
    var grantTimeRange = generateTimeRanges([400, 500, 750, 1000, 1300])
    var grantColors = ['#A7F432','#8FD400', '#03C04A', '#228C22', '#005C29', '#123524']
    
    // Generate EPM Legends (except expiring)
    let epmMoratoriumLegend = generateLegend(morTimeRange, morColors, "Expiry Date Ranges");
    let epmApplicationsLegend = generateLegend(appTimeRange, appColors, "Lodge Date Ranges");
    let epmGrantedLegend = generateLegend(grantTimeRange, grantColors, "Granted Date Ranges", legendPosition="topleft");

    // As Application and grant EPMs are displayed in the beginning
    map.addControl(epmApplicationsLegend)
    map.addControl(epmGrantedLegend)

    // Divides data among different permit types to generate selection layers
    $.getJSON("get/tenements/", function (data) {
        var epmApplications = []
        var epmGranted = []
        var epmExpiring = []
        var epmMoratorium = []
        var mdlApplications = []
        var mdlGranted = []
        var mlApplications = []
        var mlGranted = []
        var epcApplications = []
        var epcGranted = []
        var currentDate = new Date().toISOString().substring(0, 10)
        var sixMonths = new Date()
        sixMonths.setMonth(sixMonths.getMonth() + 6)
        sixMonths = sixMonths.toISOString().substring(0, 10) // for expiring layer

        data.features.forEach(function(tenement){
            switch(tenement.properties.PERMITTY_2) {                         // Match permit type
                case "EPM":
                    switch(tenement.properties.PERMITST_1) {                // Match permit status
                        case "Application":
                            epmApplications.push(tenement);
                            epmApplications[epmApplications.length - 1].properties['COLOR'] = getEPMColor(tenement.properties.LODGEDATE, appTimeRange, appColors) // get color acc to date
                                break;
            
                        case "Granted":
                            if (currentDate > tenement.properties.EXPIRYDATE){  // check if the premit is expired
                                if (tenement.properties.PERMITST_2 != "Renewal Lodged"){
                                    epmMoratorium.push(tenement);
                                    epmMoratorium[epmMoratorium.length - 1].properties['COLOR'] = getEPMColor(tenement.properties.EXPIRYDATE, morTimeRange, morColors)
                                }
                            }
                            else{
                                epmGranted.push(tenement);
                                epmGranted[epmGranted.length - 1].properties['COLOR'] = getEPMColor(tenement.properties.APPROVEDAT, grantTimeRange, grantColors)
                                if (sixMonths >= tenement.properties.EXPIRYDATE){   // checks if the permit is about to expire ( 6 months time frame )
                                    epmExpiring.push(tenement)
                                }
                            }
                                break;
                    }
                    break;
    
                case "MDL":
                    switch(tenement.properties.PERMITST_1) {
                        case "Application":
                            mdlApplications.push(tenement);
                                break;
            
                        case "Granted":
                            mdlGranted.push(tenement);
                                break;
                    }
                    break;

                case "ML":
                    switch(tenement.properties.PERMITST_1) {
                        case "Application":
                            mlApplications.push(tenement);
                                break;
            
                        case "Granted":
                            mlGranted.push(tenement);
                                break;
                    }
                    break;
                
                case "EPC":
                    switch(tenement.properties.PERMITST_1) {
                        case "Application":
                            epcApplications.push(tenement);
                                break;
                
                        case "Granted":
                            epcGranted.push(tenement);
                                break;
                    }
                    break;
            }
            
        })
        // Generate selection layers
        // EPM
        // Moratorium
        generateSelectionLayer(epmMoratorium, ["DISPLAYNAM", "EXPIRYDATE", "AUTHORIS_1"], ["Permit:", "Expired on:", "Company Name:"])
                                            .addTo(epmMoratoriumLayer);
        // Pending
        generateSelectionLayer(epmApplications, ["DISPLAYNAM", "LODGEDATE", "AUTHORIS_1"],["Permit:", "Application Date:", "Company Name:"])
                                            .addTo(epmApplicationsLayer);
        // Granted
        generateSelectionLayer(epmGranted, ["DISPLAYNAM", "APPROVEDAT", "AUTHORIS_1"],["Permit:", "Approved Date:", "Company Name:"])
                                            .addTo(epmGrantedLayer);
        // Expiring
        generateSelectionLayer(epmExpiring, ["DISPLAYNAM", "EXPIRYDATE", "AUTHORIS_1"], ["Permit:", "Expiring on:", "Company Name:"], "#FFFF00")
                                            .addTo(fillExpiringLayer);

        // MDL
        generateSelectionLayer(mdlApplications, ["DISPLAYNAM", "LODGEDATE", "AUTHORIS_1"] ,["Permit:", "Application Date:", "Company Name:"], "#000000")
            .addTo(mdlApplicationsLayer);
        generateSelectionLayer(mdlGranted, ["DISPLAYNAM", "APPROVEDAT", "AUTHORIS_1"] ,["Permit:", "Approved Date:", "Company Name:"], "#A020F0")
            .addTo(mdlGrantedLayer);

        // ML
        generateSelectionLayer(mlApplications, ["DISPLAYNAM", "LODGEDATE", "AUTHORIS_1"] ,["Permit:", "Application Date:", "Company Name:"], "#964B00")
            .addTo(mlApplicationsLayer);
        generateSelectionLayer(mlGranted, ["DISPLAYNAM", "APPROVEDAT", "AUTHORIS_1"] ,["Permit:", "Approved Date:", "Company Name:"], "#FFA500")
            .addTo(mlGrantedLayer);
        
        // EPC
        generateSelectionLayer(epcApplications, ["DISPLAYNAM", "LODGEDATE", "AUTHORIS_1"] ,["Permit:", "Application Date:", "Company Name:"], "#922B3E")
            .addTo(epcApplicationsLayer);
        generateSelectionLayer(epcGranted, ["DISPLAYNAM", "APPROVEDAT", "AUTHORIS_1"] ,["Permit:", "Approved Date:", "Company Name:"], "#0D98BA")
            .addTo(epcGrantedLayer);
    })

    // Generating data for  cadastre selection layer
    $.getJSON("cadastre", function (data) {
        generateSelectionLayer(data, ["LOT", "PLAN", "ACC_CODE"], ["LOT", "PLAN", "ACC_CODE"], "#808080")
            .addTo(cadastreLayer);
    });

    // adding epm grant and application layer for search in the beginning
    epmApplicationsLayer.addTo(searchTenementFeature);
    epmGrantedLayer.addTo(searchTenementFeature);

    // setting up selection layer display
    var selectionLayers = {
        "<span class='cadastre'>Cadastre </span>": cadastreLayer,
        "<span class='mdlApplications'>MDL Permit Applications </span>": mdlApplicationsLayer,
        "<span class='mdlGranted'>MDL Permit Granted </span>": mdlGrantedLayer,
        "<span class='mlApplications'>ML Permit Applications </span>": mlApplicationsLayer,
        "<span class='mlGranted'>ML Permit Granted </span>": mlGrantedLayer,
        "<span class='epcApplications'>EPC Permit Applications </span>": epcApplicationsLayer,
        "<span class='epcGranted'>EPC Permit Granted </span>": epcGrantedLayer,
        "<span class='moratorium'>Moratorium </span>": epmMoratoriumLayer,
        "<span class='pending'>Pending Applications </span>": epmApplicationsLayer,
        "<span class='granted'>Granted Exploration Permits </span>": epmGrantedLayer,
        "<span class='reaching'>EPM Approaching Expiry </span>": epmExpiringLayer,
    };


    // creating selection layer control
    var selectionLayerControl = L.control.layers({}, selectionLayers,
        {autoZIndex: true, position: "topright"})
    
    map.addControl(selectionLayerControl);      

    // executes when a layer is selected
    map.on('overlayadd', function (displayLayer) {

        if (displayLayer.layer !== epmExpiringLayer){              // adds layer to tenement search feature except Approaching expiry
            displayLayer.layer.addTo(searchTenementFeature);
        }           
        toolbarLayer.clearLayers();                                 // removes user shape on change in tenements

        switch(displayLayer.layer) {                                // add legend depending upon the layer added
            case epmGrantedLayer:
                    map.addControl(epmGrantedLegend);
                    map.removeLayer(epmExpiringLayer);              // Approaching expiry can only exist if EPM Granted is selected
                    fillExpiringLayer.addTo(epmExpiringLayer);      // refill Approaching Expiry layer
                    selectionLayerControl.addOverlay(epmExpiringLayer,"<span class='reaching'>EPM Approaching Expiry </span>")
                    break;

            case epmApplicationsLayer:
                    map.addControl(epmApplicationsLegend);
                    break;

            case epmMoratoriumLayer:
                    map.addControl(epmMoratoriumLegend);
                    break;
        }
    });

    // executes when a layer is de-selected
    map.on('overlayremove', function (displayLayer) {

        if (displayLayer.layer !== epmExpiringLayer){              // removes selection layer data from tenement search except Approaching expiry
            searchTenementFeature.removeLayer(displayLayer.layer);
        }       
        toolbarLayer.clearLayers()                                  // removes user shape on change in tenements

        switch(displayLayer.layer) {                                // remove legend depending upon the layer de-selected
            case epmGrantedLayer:
                    map.removeControl(epmGrantedLegend);
                    selectionLayerControl.removeLayer(epmExpiringLayer);
                    epmExpiringLayer.clearLayers()
                    break;

            case epmApplicationsLayer:
                    map.removeControl(epmApplicationsLegend);
                    break;

            case epmMoratoriumLayer:
                    map.removeControl(epmMoratoriumLegend);
                    break;
          }
    });

    // event when user creates a shape from the toolbar
    map.on(L.Draw.Event.CREATED, function (drawnShape) {

        toolbarLayer.clearLayers()                          // clear all previous layers

        drawnShape.layer.addTo(toolbarLayer);               // add the drawn shape to map

        if (drawnShape.layer instanceof L.Circle) {         // change shape instance if circle (intersection does not work on circles)
            drawnShape.layer = L.PM.Utils.circleToPolygon(drawnShape.layer, 60);
        }

        drawnShapeGJ = drawnShape.layer.toGeoJSON();        // required for intersection check

        function getIntersectedTenements(selectionLayer){   // get all MDL, ML, EPC, Cadastre's layer and row properties
            intersectedTenementRows = []
            intersectedTenementLayers = []
            // Check if layer is selected in map
            if (map.hasLayer(selectionLayer)) {
                selectionLayer.eachLayer(function (s_layer) {                           // get all layers
                    s_layer.eachLayer(function (layer) {                                // loop through each layer
                        if (turf.booleanIntersects(drawnShapeGJ, layer.toGeoJSON())) {  // check for interseaction between layer and shape
                            intersectedTenementRows.push(layer.feature.properties)      // to display in table
                            intersectedTenementLayers.push(layer)                       // to find intersections with EPMs 
                        }
                    })
                });
            }
            return [intersectedTenementRows, intersectedTenementLayers]
        }

        // get intersected tenements and thier details
        let [mdlGrantedRows, mdlGrantedLayers] = getIntersectedTenements(mdlGrantedLayer)
        let [mdlApplicationsRows, mdlApplicationsLayers] = getIntersectedTenements(mdlApplicationsLayer)
        let [mlGrantedRows, mlGrantedLayers] = getIntersectedTenements(mlGrantedLayer)
        let [mlApplicationsRows, mlApplicationsLayers] = getIntersectedTenements(mlApplicationsLayer)
        let [epcGrantedRows, epcGrantedLayers] = getIntersectedTenements(epcGrantedLayer)
        let [epcApplicationsRows, epcApplicationsLayers] = getIntersectedTenements(epcApplicationsLayer)
        let [cadastreRows, cadastreLayers] = getIntersectedTenements(cadastreLayer)

        function getTenementEPMIntersections(layer){        // adds details of tenements intersecting with EPMs in EPM tables
                                                            // tenement details are stored as list
            epm_properties = layer.feature.properties
            // MDL and EPM intersections
            epm_properties['MDL'] = '<ol>';
            mdlGrantedLayers.filter(mdl_layer => turf.booleanIntersects(mdl_layer.toGeoJSON(), layer.toGeoJSON()))
                            .forEach(mdl_layer => epm_properties['MDL'] += '<li><strong>' + mdl_layer.feature.properties.DISPLAYNAM + '</strong>: Granted on <strong>' + mdl_layer.feature.properties.APPROVEDAT + '</strong> To <strong>' + mdl_layer.feature.properties.AUTHORIS_1 + '</strong></li>');
            mdlApplicationsLayers.filter(mdl_layer => turf.booleanIntersects(mdl_layer.toGeoJSON(), layer.toGeoJSON()))
                            .forEach(mdl_layer => epm_properties['MDL'] += '<li><strong>' + mdl_layer.feature.properties.DISPLAYNAM + '</strong>:   Applied on   ' + mdl_layer.feature.properties.LODGEDATE + '</strong> By <strong>' + mdl_layer.feature.properties.AUTHORIS_1 + '</strong></li>');
            if (epm_properties['MDL'] === '<ol>'){
                epm_properties['MDL'] = null;
            }
            else{
                epm_properties['MDL'] += '</ol>';
            }
    
            // ML and EPM intersections
            epm_properties['ML'] = '<ol>';
            mlGrantedLayers.filter(ml_layer => turf.booleanIntersects(ml_layer.toGeoJSON(), layer.toGeoJSON()))
                            .forEach(ml_layer => epm_properties['ML'] += '<li><strong>' + ml_layer.feature.properties.DISPLAYNAM + '</strong>: Granted on <strong>' + ml_layer.feature.properties.APPROVEDAT + '</strong> To <strong>' + ml_layer.feature.properties.AUTHORIS_1 + '</strong></li>');
            mlApplicationsLayers.filter(ml_layer => turf.booleanIntersects(ml_layer.toGeoJSON(), layer.toGeoJSON()))
                            .forEach(ml_layer => epm_properties['ML'] += '<li><strong>' + ml_layer.feature.properties.DISPLAYNAM + '</strong>:   Applied on   ' + ml_layer.feature.properties.LODGEDATE  + '</strong> By <strong>' + ml_layer.feature.properties.AUTHORIS_1 + '</strong></li>');
            if (epm_properties['ML'] === '<ol>'){
                epm_properties['ML'] = null;
            }
            else{
                epm_properties['ML'] += '</ol>';
            }

            // EPC and EPM intersections
            epm_properties['EPC'] = '<ol>';
            epcGrantedLayers.filter(epc_layer => turf.booleanIntersects(epc_layer.toGeoJSON(), layer.toGeoJSON()))
                            .forEach(epc_layer => epm_properties['EPC'] += '<li><strong>' + epc_layer.feature.properties.DISPLAYNAM + '</strong>: Granted on <strong>' + epc_layer.feature.properties.APPROVEDAT + '</strong> To <strong>' + epc_layer.feature.properties.AUTHORIS_1 + '</strong></li>');
            epcApplicationsLayers.filter(epc_layer => turf.booleanIntersects(epc_layer.toGeoJSON(), layer.toGeoJSON()))
                            .forEach(epc_layer => epm_properties['EPC'] += '<li><strong>' + epc_layer.feature.properties.DISPLAYNAM + '</strong>:   Applied on   ' + epc_layer.feature.properties.LODGEDATE  + '</strong> By <strong>' + epc_layer.feature.properties.AUTHORIS_1 + '</strong></li>');
            if (epm_properties['EPC'] === '<ol>'){
                epm_properties['EPC'] = null;
            }
            else{
                epm_properties['EPC'] += '</ol>';
            }
    
            // CADASTRE and EPM intersections
            epm_properties['CADASTRE'] = '<ol>';
            cadastreLayers.filter(c_layer => turf.booleanIntersects(c_layer.toGeoJSON(), layer.toGeoJSON()))
                            .forEach(c_layer => epm_properties['CADASTRE'] += '<li>' + c_layer.feature.properties.LOT + ' / ' + c_layer.feature.properties.PLAN + '</li>');
            if (epm_properties['CADASTRE'] === '<ol>'){
                epm_properties['CADASTRE'] = null;
            }
            else{
                epm_properties['CADASTRE'] += '</ol>';
            }
    
            return epm_properties
        }
        
        function getIntersectedEPM(selectionLayer){         // find intersected EPMs and fetch their table data
            intersectedEPMRows = []
            // Check for active layers and add overlappping data to table
            if (map.hasLayer(selectionLayer)) {                                         
                selectionLayer.eachLayer(function (s_layer) {                           // get all layers
                    s_layer.eachLayer(function (layer) {                                // loop through each layer
                        if (turf.booleanIntersects(drawnShapeGJ, layer.toGeoJSON())) {  // check for interseaction between layer and shape
                            intersectedEPMRows.push(getTenementEPMIntersections(layer))      // to display in table
                        }
                    })
                });
            }
            return intersectedEPMRows
        }
        
        // get intersected EPMs and their tenement details
        let epmApplicationsRows = getIntersectedEPM(epmApplicationsLayer);
        let epmGrantedRows = getIntersectedEPM(epmGrantedLayer);

        // Repopulate tables with data
        epmGrantedTable.clear().draw();                             // EPM Granted
        epmGrantedTable.rows.add(epmGrantedRows).draw();

        epmApplicationsTable.clear().draw();                        // EPM Applicaitons
        epmApplicationsTable.rows.add(epmApplicationsRows).draw();

        mdlGrantedTable.clear().draw();                             // MDL Granted
        mdlGrantedTable.rows.add(mdlGrantedRows).draw();

        mdlApplicationsTable.clear().draw();                        // MDL Applications
        mdlApplicationsTable.rows.add(mdlApplicationsRows).draw();

        mlGrantedTable.clear().draw();                              // ML Granted
        mlGrantedTable.rows.add(mlGrantedRows).draw();

        mlApplicationsTable.clear().draw();                         // ML Applicaitons
        mlApplicationsTable.rows.add(mlApplicationsRows).draw();

        epcApplicationsTable.clear().draw();                         // EPC Applicaitons
        epcApplicationsTable.rows.add(epcApplicationsRows).draw();

        epcGrantedTable.clear().draw();                              // EPC Granted
        epcGrantedTable.rows.add(epcGrantedRows).draw();

        cadastreTable.clear().draw();                               // Cadastre
        cadastreTable.rows.add(cadastreRows).draw();

        // Change text displayed on map footer with results found
        if (epmGrantedTable.rows().count() + epmApplicationsTable.rows().count() 
            + mdlGrantedTable.rows().count() + mdlApplicationsTable.rows().count() 
            + mlGrantedTable.rows().count() + mlApplicationsTable.rows().count() 
            + epcGrantedTable.rows().count() + epcApplicationsTable.rows().count()
            + cadastreTable.rows().count() > 0) {                   // if any tenement is selected except epm moratorium
            updateTableHeaders();
            $("#table-panel").slideDown();
        } else {                                                    // if no results are found
            $("#map-footer").empty();
            $("#map-footer").append(`No Results Found`);
            $("#table-panel").slideUp();
        }
    });

    $('#sidebarToggleButton').on('click',function (e) {             // resize map if side bar changes size
        setTimeout(function(){map.invalidateSize()}, 200);
    });
});