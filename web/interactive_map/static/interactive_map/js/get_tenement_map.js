// Merge all the features into the map and return
function generate_tenement_map(tenement_list, target_list, tenement_data) {
    //Setting up the map
    const tenement_map = L.map("tenement_map", {
      zoomControl: false,
      attributionControl: false,
    }).setView([-19.917574, 143.702789], 5);
  
    //Setting Up Map Display
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution:
        '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(tenement_map);
  
    var geojson_feature = new L.FeatureGroup().addTo(tenement_map);
    
    // all four application files are searched to fetch data belonging to the tenenment
    tenement_list.every((tenement) => {

      // each tenement is checked
      tenement_data.eachLayer(function (layer) {
          // if tenement found
          if (layer.feature.properties.DISPLAYNAM === tenement.tenement_permit) {
  
            // create tenement object to be displayed on map
            geojson_layer = L.geoJson(layer.feature, {
              style: function (feature) {
                return { color: layer.feature.properties.COLOR }; // assign color to tenement
              },
              onEachFeature: function onEachFeature(feature, layer) {
                layer.on({
                  // Zoom on click Function
                  click: function zoomToFeature(e) {
                    tenement_map.fitBounds(e.target.getBounds());
                  },
                });
                layer.bindTooltip(
                  // tooltip to display tenement information on map
                  function (layer) {
                    let div = L.DomUtil.create("div");
  
                    let handleObject = (feature) =>
                      typeof feature == "object"
                        ? JSON.stringify(feature)
                        : feature;
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
                          
                          <td>${handleObject(layer.feature.properties[v])}</td>
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
            }).addTo(geojson_feature); // tenement added to feature
            return false; // stop the search
          }
          return true; // continue search
        });
      return true;
    });
  
    if (target_list.length != 0){
      target_list.every((target) => {
        var coordinates = target.location.split(" ");
        var marker = L.marker([+coordinates[0], +coordinates[1]]);
        geojson_feature.eachLayer(function (layer) {
          if (turf.booleanIntersects(marker.toGeoJSON(), layer.toGeoJSON())) {
            marker.addTo(geojson_feature)
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
          }
        });
        return true
      });
    }
    tenement_map.fitBounds(geojson_feature.getBounds());
    return tenement_map;
}
  
function get_intersected_targets(tenement, target_list, tenement_data){

  //Setting up the map
  var intersected_targets = []

  // pending application file is searched to find the tenement
  tenement_data.eachLayer(function (layer) {
      // if tenement found
      if (layer.feature.properties.DISPLAYNAM === tenement) {
        if (target_list.length != 0){
          target_list.every((target) => {
            var coordinates = target.location.split(" ");
            var marker = L.marker(coordinates);
            if (turf.booleanIntersects(marker.toGeoJSON(), layer.toGeoJSON())) {
                target.location = "[ " + coordinates[0] +", " + coordinates[1] + " ]"
                intersected_targets.push(target);
              }
            return true
          });
          }
        return false; // stop the search
      }
      return true; // continue search
    });

return intersected_targets;
}