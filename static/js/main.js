/* main.js */
// Initialize map variables
var mapCenterLatitude = 37.7749;
var mapCenterLongitude = -122.4194;
var mapZoomLevel = 13;

// Initialize the map
var map = L.map('map').setView([mapCenterLatitude, mapCenterLongitude], mapZoomLevel);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Create a GeoJSON layer for the lanes
var lanesLayer = L.geoJSON(null, {
    style: function(feature) {
        return { color: 'blue', weight: 2 };
    },
    onEachFeature: function(feature, layer) {
        var popupContent = '<strong>ID:</strong> ' + feature.properties.id + '<br>' +
                          '<strong>Type Names:</strong> ' + feature.properties.type_names + '<br>' +
                          '<strong>Semantic Description:</strong> ' + feature.properties.semantic_description;
        layer.bindPopup(popupContent);
    }
}).addTo(map);

function loadLanes() {
    var type_names = $('#type_names').val();
    var semantic_description = $('#semantic_description').val();
    var params = {};
    
    if (type_names) params.type_names = type_names;
    if (type_names === 'Lane Nominal' && semantic_description) {
        params.semantic_description = semantic_description;
    }

    // Use relative URL instead of hardcoded localhost
    $.ajax({
        url: '/api/lanes',
        data: params,
        success: function(data) {
            lanesLayer.clearLayers();
            if (data.features && data.features.length > 0) {
                lanesLayer.addData(data);
                map.fitBounds(lanesLayer.getBounds());
            } else {
                alert('No lanes found for the given filters.');
            }
        },
        error: function(err) {
            console.error('Error fetching data:', err);
            alert('An error occurred while fetching lane data.');
        }
    });
}

$('#filterBtn').click(function() {
    loadLanes();
});

// Initial load
loadLanes();