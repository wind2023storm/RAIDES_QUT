$(document).ready(function () {

    $.getJSON('get/tenements_json/', function (tenement_data) {

      var tenement_list = JSON.parse($('#id_tenements').val())

        //Setting up the map
      const target_map = L.map("target_map", {
        //zoomControl: false,
        attributionControl: false,
      }).setView([-19.917574, 143.702789], 5);

      //Setting Up Map Display
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        // minZoom: 5,
        maxZoom: 19,
        attribution:
          '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(target_map);

      var geojson_feature = new L.FeatureGroup().addTo(target_map);

      function generate_layer(layer){
        // create tenement object to be displayed on map
        geojson_layer = L.geoJson(layer.feature, {
          style: function (feature) {
            return { color: feature.properties.COLOR }; // assign color to tenement
          },
          onEachFeature: function onEachFeature(feature, layer) {
            layer.on({
              // Zoom on click Function
              click: function zoomToFeature(e) {
                target_map.fitBounds(e.target.getBounds());
              },
            });
            layer.bindTooltip(
              // tooltip to display tenement information on map
              function (layer) {
                let div = L.DomUtil.create("div");

                let fields = (layer.feature.properties['PERMITST_1'] === "Application") ? ["DISPLAYNAM", "LODGEDATE", "AUTHORIS_1"] : ["DISPLAYNAM", "APPROVEDAT", "AUTHORIS_1"]; //Geojson file data properties
                let aliases = (layer.feature.properties['PERMITST_1'] === "Application") ? ["Permit:", "Application Date:", "Company Name:"] : ["Permit:", "Approved Date:", "Company Name:"]; //Name to display above properties args
                let table =
                  "<table>" +
                  String(
                    fields
                      .map(
                        (v, i) =>
                          `<tr>
                      <th>${aliases[i]}</th>
                      
                      <td>${layer.feature.properties[v]}</td>
                    </tr>`
                      )
                      .join("")
                  ) +
                  "</table>";
                div.innerHTML = table;
                return div;
              },
              {
                // tooltip styling
                sticky: true,
                className: "foliumtooltip",
              }
            );
          },
        })
        return geojson_layer
      }
      var geojson_data = [];

      tenement_list.every((tenement) => {

        var tenement_key = tenement.type + tenement.status
        var tenement_name = tenement.type + " " + tenement.number
        Object.entries(tenement_data).forEach(([key, value]) => {
          if (key === tenement_key){
            if(!geojson_data.includes(key)){
              tenement_data[key] = L.geoJson(value)
              geojson_data.push(key)
            }
            // each tenement is checked
            tenement_data[key].eachLayer(function (layer) {
              // if tenement found
              if (layer.feature.properties.DISPLAYNAM === tenement_name) {

                generate_layer(layer).addTo(geojson_feature); // tenement added to feature
                
                return false; // stop the search
              }
              return true; // continue search
            });
          }
        });
        return true;
      });
      var markerLayer = new L.FeatureGroup().addTo(target_map);

      $('#addTargetButton').on('click',function (e) {
            
        setTimeout(function(){ target_map.invalidateSize(); target_map.fitBounds(geojson_feature.getBounds());}, 200);
        $('#id_target_id').val('');
        $('#id_target_name').val('');
        $('#id_target_description').val('');
        $('#id_location').val('');
        $('#id_location_input').val('');
        $('#addEditTargetForm .modal-header').text('Add Prospect');
        $('#addEditTargetForm #btnSubmit').text('Add');
        markerLayer.clearLayers();
        target_map.fitBounds(geojson_feature.getBounds()); 
      });

      $('#target-table').on('click', 'button:has(.fa-pen)', function (e) {
        setTimeout(function(){ target_map.invalidateSize()}, 200);
        let tableRow = $('#target-table').DataTable().row($(this).parents('tr')).data();
        let location = tableRow['location'].replace(/(\[|\]|,)/gm,'')
        location = location.trim();
        $('#id_target_id').val(tableRow['name']);
        $('#id_target_name').val(tableRow['name']);
        $('#id_target_description').val(tableRow['description']);
        $('#id_location').val(location);
        $('#id_location_input').val(location);
        $('#addEditTargetForm .modal-header').text('Edit Prospect');
        $('#addEditTargetForm #btnSubmit').text('Save');
        var coordinates = location.split(" ")
        markerLayer.clearLayers();
        L.marker(coordinates).addTo(markerLayer);
        
        if (tableRow['permit'].type === null){
            target_map.setView(coordinates, 7);
        }
        else{
            var permit_id = tableRow['permit'].type + " " + tableRow['permit'].number
            geojson_feature.eachLayer(function (s_layer) {                           // get all layers
                s_layer.eachLayer(function (layer) {
                    if (layer.feature.properties.DISPLAYNAM === permit_id) {
                        setTimeout(function(){ target_map.fitBounds(layer._bounds);}, 200); 
                    }
                })
            });
        }
        
    });

      target_map.on('click', function (e) {
        
        markerLayer.clearLayers(); 
        
        var marker = L.marker([e.latlng.lat, e.latlng.lng]).addTo(markerLayer);
        marker.bindPopup(`Latitude: ${e.latlng.lat}  
                          Longitude: ${e.latlng.lng}`).openPopup();

        $('#id_location').val(`${e.latlng.lat} ${e.latlng.lng}`);
        $('#id_location_input').val(`${e.latlng.lat} ${e.latlng.lng}`);
      });
    });
  });