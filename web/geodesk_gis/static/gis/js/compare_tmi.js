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

function updateImages(comp_img_path) {
    const randomNumber1 = Math.floor(Math.random() * 1000);
    const selectedImageUrl = `/static/gis/img/to_display/img.png?rand=${randomNumber1}`;
    document.getElementById('selectedImage').src = selectedImageUrl;

    const randomNumber2 = Math.floor(Math.random() * 1000);
    const comparedImageUrl = `/static/gis/img/to_compare/img.png?rand=${randomNumber2}`;
    document.getElementById('comparedImage').src = comparedImageUrl;
}

var zoomLevel;
var scale;
var selected_latitude;
var selected_longitude;
var current_history = null;
var history_flag = false;
var markers = [];

document.getElementById('zoom5km').addEventListener('click', function () {
    zoomLevel = 11;
    scale = "5km";
    console.log("5km selected")
    updateMapZoom(zoomLevel);
});

document.getElementById('zoom10km').addEventListener('click', function () {
    zoomLevel = 10;
    scale = "10km";
    console.log("10km selected")
    updateMapZoom(zoomLevel);
});

document.getElementById('zoom20km').addEventListener('click', function () {
      zoomLevel = 9;
      scale = "20km";
      console.log("20km selected")
      updateMapZoom(zoomLevel);
});

/* When click 'back' button */
document.getElementById('back').addEventListener('click', function () {
    $.ajax({
        headers: {"X-CSRFToken": csrf_token},
        url: 'http://localhost:8000/gis/back_history',
        type: 'POST',
        data: {
            'current_history': current_history,
            'csrfmiddlewaretoken': csrf_token
        },
        dataType: "json",
        success: function(response) {
            if (response.flag == true) {
                alert('This is end result!')
                return;
            }
            current_history = response.backResults.no;
            prev_lat = response.backResults.latitude;
            prev_long = response.backResults.longitude;
            pre_zoom = response.backResults.zoom;
            updateMapZoomAndCoords(prev_lat, prev_long, pre_zoom)
        },
        error: function(xhr, errmsg, err) {
            alert('There are no results!')
        }
    })
});

/* When click 'forward' button */
document.getElementById('forward').addEventListener('click', function () {
    $.ajax({
        headers: {"X-CSRFToken": csrf_token},
        url: 'http://localhost:8000/gis/forward_history',
        type: 'POST',
        data: {
            'current_history': current_history,
            'csrfmiddlewaretoken': csrf_token
        },
        dataType: "json",
        success: function(response) {
            if (response.flag == true) {
                alert('This is first result!')
                return;
            }
            current_history = response.forwardResults.no;
            prev_lat = response.forwardResults.latitude;
            prev_long = response.forwardResults.longitude;
            pre_zoom = response.forwardResults.zoom;
            updateMapZoomAndCoords(prev_lat, prev_long, pre_zoom)
        },
        error: function(xhr, errmsg, err) {
            alert('There are no results!');
        }
  })
});


function updateMapZoom(zoomLevel) {
    map.setView(new L.LatLng(-33.888677964124916, 143.99230957031253), zoomLevel);
}

function updateMapZoomAndCoords(latitude, longitude, zoomLevel) {
    history_flag = true;
    if (zoomLevel == null)
        zoomLevel = 6;
    map.setView(new L.LatLng(latitude, longitude), zoomLevel);
    selected_latitude = latitude;
    selected_longitude = longitude;
    detailMap();
}

function detailMap () {
    document.getElementById('startMessage').style.display = 'none';
    document.getElementById('loadingBar').style.display = 'block';
    document.getElementById('loadingBg').style.display = 'block';

    var tileCoordinates = convertLatLngToTile(selected_latitude, selected_longitude, zoomLevel);
    var similarityResult;

    /* Get similarity result */
    $.ajax({
        headers: {"X-CSRFToken": csrf_token},
        url: 'http://localhost:8000/gis/output_model_result',
        type: 'POST',
        data: {
            'latitude': selected_latitude,
            'longitude': selected_longitude,
            "scale" : scale,
            'csrfmiddlewaretoken': csrf_token
        },
        dataType: "json",
        success: function(response) {
            var modelResult = response.model_result;
            var path_to_compared_image = response.path_to_compared_image;

            similarityResult = response.similarity_result;
            if (modelResult) {
                var modelResultTextElement = document.getElementById('modelResultText');

                modelResultTextElement.textContent = "Model Result: " + modelResult;
                updateImages(path_to_compared_image);
                document.getElementById('scale').textContent = scale;
                document.getElementById('latitude').textContent = selected_latitude;
                document.getElementById('longitude').textContent = selected_longitude;

                var tileMarker = L.icon({
                    iconUrl: '/static/gis/img/location_marker_4.png',
                    iconSize: [64, 64],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32]
                });

                var marker = L.marker([selected_latitude, selected_longitude], {
                    icon: tileMarker
                }).addTo(map);

                marker.bindPopup(modelResult).openPopup();
                markers.push(marker)

                map.setView(new L.LatLng(selected_latitude, selected_longitude), zoomLevel);
            }

            /* Save result */
            if (history_flag == false) {
                $.ajax({
                    headers: {"X-CSRFToken": csrf_token},
                    url: 'http://localhost:8000/gis/store_results',
                    type: 'POST',
                    data: {
                        'latitude_to_store': selected_latitude,
                        'longitude_to_store': selected_longitude,
                        'similarity_to_store': similarityResult,
                        "scale_to_store" : scale,
                        "zoom_lvl": zoomLevel,
                        'csrfmiddlewaretoken': csrf_token
                    },
                    dataType: "json",
                    success: function(response) {
                        updateTable(response.searchResults);
                        console.log("data is sent");
                        console.log("2SIM Model Result:", similarityResult);
                    },
                    error: function(xhr, errmsg, err) {
                        console.log("Error:", errmsg);
                    }
                });
            }

            document.getElementById('loadingBar').style.display = 'none';
            document.getElementById('loadingBg').style.display = 'none';
            

        },

        error: function(xhr, errmsg, err) {
            console.log("Error:", errmsg);
        }
    });

    /* */
    $.ajax({
        headers: {"X-CSRFToken": csrf_token},
        url: 'http://localhost:8000/gis/extract_image',
        type: 'POST',
        data: {
            'tile_X': tileCoordinates.x,
            'tile_Y': tileCoordinates.y,
            'zoom_lvl' : zoomLevel,
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

    /* */
    var resultSection = document.getElementById("instanceResults");

    resultSection.style.display = "block";
    document.getElementById('latitude').textContent = "Loading...";
    document.getElementById('longitude').textContent = "Loading...";

    const showResultsButton = document.getElementById('showResultsButton');
}

$(window).on("map:init", function (event) {
    map = event.detail.map;
    map.doubleClickZoom.disable();
    map.setView(new L.LatLng(-32.372035, 143.67483653), 6);
    addTileOverlay();

    map.on('dblclick', function(event) {
        selected_latitude = event.latlng.lat;
        selected_longitude = event.latlng.lng;
        history_flag == false;
        detailMap();
    })
})


/* Update table modal */
function updateTable(searchResults) {
    const tableBody = document.querySelector('#resultsTableContainer tbody');
    tableBody.innerHTML = '';

    searchResults.forEach(function(result) {
        const row = document.createElement('tr');
        const cell1 = document.createElement('td');
        cell1.textContent = result.latitude;
        const cell2 = document.createElement('td');
        cell2.textContent = result.longitude;

        const cell3 = document.createElement('td');
        cell3.textContent = result.scale;

        const cell4 = document.createElement('td');
        cell4.textContent = result.similarity;

        row.appendChild(cell1);
        row.appendChild(cell2);
        row.appendChild(cell3);
        row.appendChild(cell4);

        tableBody.appendChild(row);
    });
}

/* */
function showRankingTable() {
    const showResultsButton = document.getElementById('showResultsButton');
    const resultsTableContainer = document.getElementById('resultsTableContainer');

    showResultsButton.addEventListener('click', function () {
        if (resultsTableContainer.style.display === 'none') {
        resultsTableContainer.style.display = 'block';
        } else {
        resultsTableContainer.style.display = 'none';
        }
    });
}

function clearResult() {
    $.ajax({
        headers: {"X-CSRFToken": csrf_token},
        url: 'http://localhost:8000/gis/clear_results',
        type: 'POST',
        data: {
            'csrfmiddlewaretoken': csrf_token
        },
        dataType: "json",
        success: function(response) {
            updateTable(response.searchResults);
            for(let i = 0; i< markers.length; i++)
                markers[i].remove();
            markers = [];
        },
        error: function(xhr, errmsg, err) {
            console.log("Error:", errmsg);
        }
    });
}