// Merge all the features into the map and return
function generate_project_map(tenement_list, target_list, tenement_data) {
  //Setting up the map
  const project_map = L.map("project_map", {
    zoomControl: false,
    attributionControl: false,
  }).setView([-19.917574, 143.702789], 5);

  //Setting Up Map Display
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(project_map);

  var geojson_feature = new L.FeatureGroup().addTo(project_map);

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
            project_map.fitBounds(e.target.getBounds());
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

    var tenement_key = tenement.permit_type + tenement.permit_status
    var tenement_name = tenement.permit_type + " " + tenement.permit_number
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

  if (target_list.length != 0){
  target_list.every((target) => {
    var coordinates = target.location.split(" ");
    L.marker(coordinates).addTo(geojson_feature)
      .bindTooltip(`<table>
                    <tr>
                      <th>Name:</th>
                      <td>${target.name}</td>
                    </tr>
                    <tr>
                      <th>Latitude:</th>
                      <td>${+coordinates[0]}</td>
                    </tr>
                    <tr>
                      <th>Longitude:</th>
                      <td>${+coordinates[1]}</td>
                    </tr>
                    <tr>
                      <th>Description:</th>
                      <td>${target.description}</td>
                    </tr>
                  </table>`,
                  {
                    
                    sticky: true,
                    className: "foliumtooltip",
                  });
    return true;
  });
}
  project_map.fitBounds(geojson_feature.getBounds());
  return project_map;
}


function get_intersected_tenements(tenement_list, target, tenement_data){

  var intersected_tenement={};
  // all four application files are searched to fetch data belonging to the project's tenenments
    tenement_list.every((tenement) => {
      let tenement_id = tenement.type + " " + tenement.number
      // pending application file is searched to find the tenement
      tenement_data.eachLayer(function (layer) {
            if (layer.feature.properties.DISPLAYNAM === tenement_id) {
                // check if tenement is within shape drawn
                if (turf.booleanIntersects(target, layer.toGeoJSON())) {
                    intersected_tenement =  tenement
                }
            }
        });

      return true;
    });
  return intersected_tenement
}
