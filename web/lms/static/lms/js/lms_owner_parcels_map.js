styles = {
  project:
  {
    weight: 2,
    fillOpacity: 0.2,
    color: "#666666"
  },
  normal: {
    weight: 2,
    fillOpacity: 0.5,
    color: "#a6b6cd"
  },
  selected: {
    weight: 2,
    fillOpacity: 0.3,
    color: "red"
  },
  hover: {
    weight: 7,
    fillOpacity: 0.6
  }
}


/**
 * 
 */
function generateOwnerParcelsMap(map, parcelsFeature) {
  console.log('Generate parcel maps');
  console.log(parcelsFeature);
  VIEW_ZOOM = 13

  projectL = L.geoJSON(parcelsFeature.project_geometry, {
      style: function(feature) {
        return styles.project
      },
      
  }).addTo(map)
  
  ownerParcelsLayer = L.geoJSON(parcelsFeature, {
    style: function(feature) {
      return styles.normal
    },
    onEachFeature: onEachFeature
  }).addTo(map)

  function onEachFeature(feature, layer) {
    layer._leaflet_id = feature.properties.id

    layer.on({
      mouseover: function (e) {
        layer.setStyle(styles.hover);
      
        if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
          layer.bringToFront();
        }
      },
      mouseout: function (e) {
        // geojsonLayer.resetStyle(layer);
        layer.setStyle(styles.normal);
      },
      // Zoom to Tenement when it is clicked
      click: function (e) {
          // lot_map.fitBounds(e.target.getBounds());
  
          
      },
    });
  
    layer.bindTooltip(`${feature.properties.lot}/${feature.properties.plan}`, {
    
      direction: 'center'
    })
  } 
  
}