var map;

function addTileOverlay() {
    L.tileLayer('/static/gis/img/output/{z}/{x}/{y}.png', {
        minZoom: 2,
        maxZoom: 18,
        attribution: 'ESO/INAF-VST/OmegaCAM',
        tms: true,
        bounds: [
            new L.LatLng(-37.368002734080335, 140.5029985763527),
            new L.LatLng(-28.145396997322745, 153.61338977456407)
        ]
    }).addTo(map);
    imageBounds = [[-29, 138], [-11.9, 153.6]];
    L.control.scale().addTo(map);

}

function convertLatLngToTile(lat, lng, zoom) {
  // Assuming your map has a tileSize of 256 pixels (standard for many tile systems)
  var tileSize = 256;

  // Calculate the scale factor based on the zoom level
  var scale = Math.pow(2, zoom);

  // Convert latitude and longitude from degrees to radians
  var latRad = lat * (Math.PI / 180);
  var lngRad = lng * (Math.PI / 180);

  // Calculate pixel coordinates
  var pixelX = ((lng + 180) / 360) * tileSize * scale;
  var pixelY = (1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) * (tileSize / 2) * scale;

  // Calculate tile coordinates by dividing pixel coordinates by tileSize
  var tileX = Math.floor(pixelX / tileSize);
  var tileY = Math.floor(pixelY / tileSize);

  // Adjust tile Y coordinate for TMS (Tile Map Service) convention
  // In TMS, Y origin is at the bottom, so we need to invert it
  tileY = (Math.pow(2, zoom) - 1) - tileY;

  return { x: tileX, y: tileY, z: zoom };
}

function updateImage() {
    const randomNumber = Math.floor(Math.random() * 1000);
    const imageUrl = `/static/gis/img/to_display/img.png?rand=${randomNumber}`;
    document.getElementById('selectedImage').src = imageUrl;
    }




$(window).on("map:init", function (event) {
    map = event.detail.map;
    map.doubleClickZoom.disable();
    addTileOverlay();
    map.setView(new L.LatLng(-32.37203571087116, 143.67483653628386), 9);



    map.on('dblclick', function(event) {
        var selected_latitude = event.latlng.lat;
        var selected_longitude = event.latlng.lng;

        console.log("Lat, Lon : " + selected_latitude + ", " + selected_longitude);

        var lat = selected_latitude;
        var lng = selected_longitude;


        var zoomLevel = 10;

        var tileCoordinates = convertLatLngToTile(selected_latitude, selected_longitude, zoomLevel);
        console.log('Tile Coordinates - X:', tileCoordinates.x, 'Y:', tileCoordinates.y, 'Z:', tileCoordinates.z);


        $.ajax({
            url: 'http://127.0.0.1:8000/gis/output_model_result',
            type: 'POST',
            data: {
                'latitude': selected_latitude,
                'longitude': selected_longitude,
                'csrfmiddlewaretoken': csrf_token
            },
            dataType: "json",
            success: function(response) {
                var modelResult = response.model_result;
                console.log("Model Result:", modelResult);

                if (modelResult) {
                    var modelResultTextElement = document.getElementById('modelResultText');
                    modelResultTextElement.textContent = "Model Result: " + modelResult;


/*                    var textIcon = L.divIcon({
                        className: 'text-icon',
                        html: '<div class="text-label" ><img src="/static/gis/img/location_marker_2.png" alt="Marker Image">' + modelResult + '</div>'
                    });*/

                    updateImage();

                    document.getElementById('latitude').textContent = selected_latitude;
                    document.getElementById('longitude').textContent = selected_longitude;

                    var tileMarker = L.icon({
                        iconUrl: '/static/gis/img/location_marker_4.png',
                        // need to change
                        iconSize: [64, 64],
                        iconAnchor: [16, 32],
                        popupAnchor: [0, -32]
                    });

                    var polygon = L.polygon([
                        [51.509, -0.08],
                        [51.503, -0.06],
                        [51.51, -0.047]
                    ]).addTo(map);


                    var marker = L.marker([selected_latitude, selected_longitude], {
                        icon: tileMarker
                    }).addTo(map);

                    marker.bindPopup(modelResult).openPopup();

                    map.setView(new L.LatLng(selected_latitude, selected_longitude), 10);
                }
            },
            error: function(xhr, errmsg, err) {
                console.log("Error:", errmsg);
            }
        });

        $.ajax({
            url: 'http://127.0.0.1:8000/gis/extract_image',
            type: 'POST',
            data: {
                'tile_X': tileCoordinates.x,
                'tile_Y': tileCoordinates.y,
                'csrfmiddlewaretoken': csrf_token
            },
            dataType: "json",
            success: function(response) {
                console.log("coordinates are sent");
            },
            error: function(xhr, errmsg, err) {
                console.log("Error:", errmsg);
            }
        });
    });
});



////// Dummy input selection

/*
function handleInputSelection() {
    event.preventDefault();

    var selectedMethod = document.querySelector('input[name="area_selection_js"]:checked');
    var outputDiv = document.getElementById("selected-option-output_js");

    if (selectedMethod) {
        var selectedValue = selectedMethod.value;
        if (selectedValue === "Upload_js") {
            outputDiv.innerHTML = "You have selected to upload .shp file";
        } else if (selectedValue === "Enter_js") {
            outputDiv.innerHTML = "You have selected to enter the coordinates";

        } else if (selectedValue === "Select_js") {
            outputDiv.innerHTML = "You have selected to select area on the map";
        }
    }
     else {
        outputDiv.innerHTML = "No selection has been made";
    }
}
*/

/*document.getElementById("submit3").addEventListener("click", handleInputSelection);*/





