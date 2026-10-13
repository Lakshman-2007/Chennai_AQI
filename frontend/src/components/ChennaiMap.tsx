import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, CircleMarker, GeoJSON, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import type { StationInfo, PredictionPoint, HotspotInfo, LocalityItem } from '../types/api';
import { fetchLocalities, fetchWardsGeoJSON } from '../services/api';
import { Search, RotateCcw } from 'lucide-react';

const createStationMarker = (color: string) => {
  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `<div style="background-color: ${color}; width: 22px; height: 22px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 0 12px ${color};"></div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11]
  });
};

const createLocalityPin = () => {
  return L.divIcon({
    className: 'custom-locality-marker',
    html: `<div style="background-color: #F59E0B; width: 16px; height: 16px; border-radius: 4px; border: 2px solid #ffffff; box-shadow: 0 0 8px #F59E0B; transform: rotate(45deg);"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });
};

interface ChennaiMapProps {
  stations?: StationInfo[];
  gridPoints?: PredictionPoint[];
  hotspots?: HotspotInfo[];
  showGrid?: boolean;
  showHotspots?: boolean;
  showStations?: boolean;
  showWards?: boolean;
  showSatelliteOverlay?: boolean;
  onMapClick?: (lat: number, lon: number) => void;
  selectedLocation?: { latitude: number; longitude: number } | null;
}

const MapController: React.FC<{
  targetCoords: [number, number] | null;
  onMapClick?: (lat: number, lon: number) => void;
}> = ({ targetCoords, onMapClick }) => {
  const map = useMap();

  useEffect(() => {
    if (targetCoords) {
      map.flyTo(targetCoords, 14, { duration: 1.2 });
    }
  }, [targetCoords, map]);

  useMapEvents({
    click(e) {
      if (onMapClick) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    }
  });

  return null;
};

export const ChennaiMap: React.FC<ChennaiMapProps> = ({
  stations = [],
  gridPoints = [],
  hotspots = [],
  showGrid = true,
  showHotspots = true,
  showStations = true,
  showWards = true,
  showSatelliteOverlay = false,
  onMapClick,
  selectedLocation = null
}) => {
  const chennaiCenter: [number, number] = [13.0427, 80.2407];
  const [mapTarget, setMapTarget] = useState<[number, number] | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<LocalityItem[]>([]);
  const [selectedLocality, setSelectedLocality] = useState<LocalityItem | null>(null);
  const [wardsData, setWardsData] = useState<any>(null);

  useEffect(() => {
    fetchWardsGeoJSON()
      .then((data) => setWardsData(data))
      .catch((err) => console.error('Failed to load wards GeoJSON', err));
  }, []);

  useEffect(() => {
    if (searchQuery.trim().length > 1) {
      fetchLocalities(searchQuery)
        .then((res) => setSearchResults(res))
        .catch(() => setSearchResults([]));
    } else {
      setSearchResults([]);
    }
  }, [searchQuery]);

  const handleSelectLocality = (loc: LocalityItem) => {
    setSelectedLocality(loc);
    setMapTarget([loc.latitude, loc.longitude]);
    setSearchResults([]);
    setSearchQuery(loc.canonical_name);
    if (onMapClick) {
      onMapClick(loc.latitude, loc.longitude);
    }
  };

  const resetToChennai = () => {
    setMapTarget(chennaiCenter);
    setSelectedLocality(null);
    setSearchQuery('');
  };

  return (
    <div className="w-full h-full min-h-[520px] rounded-3xl overflow-hidden border border-slate-800 shadow-2xl relative flex flex-col">
      {/* Top Floating Search & Controls Bar */}
      <div className="absolute top-4 left-4 right-4 z-[1000] flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        {/* Search input with autocomplete */}
        <div className="relative pointer-events-auto w-full max-w-md">
          <div className="flex items-center bg-slate-900/95 backdrop-blur-md border border-slate-700/80 rounded-2xl px-3 py-2 shadow-xl">
            <Search className="w-4 h-4 text-indigo-400 mr-2 shrink-0" />
            <input
              type="text"
              placeholder="Search Chennai locality (e.g. T. Nagar, Adyar, Velachery)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent text-xs text-white placeholder-slate-400 focus:outline-none w-full"
            />
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSearchResults([]);
                }}
                className="text-xs text-slate-400 hover:text-white ml-1 px-1"
              >
                ✕
              </button>
            )}
          </div>

          {/* Autocomplete Dropdown */}
          {searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-slate-900/95 backdrop-blur-md border border-slate-700 rounded-2xl shadow-2xl overflow-hidden max-h-60 overflow-y-auto z-[1001]">
              {searchResults.map((loc, idx) => (
                <div
                  key={`loc-${idx}`}
                  onClick={() => handleSelectLocality(loc)}
                  className="px-3 py-2.5 hover:bg-indigo-600/20 cursor-pointer border-b border-slate-800/60 last:border-0 flex items-center justify-between"
                >
                  <div>
                    <div className="text-xs font-bold text-white">{loc.canonical_name}</div>
                    <div className="text-[10px] text-slate-400">{loc.zone} • {loc.type}</div>
                  </div>
                  {loc.has_ground_station ? (
                    <span className="text-[10px] bg-emerald-500/20 text-emerald-300 font-semibold px-2 py-0.5 rounded-full border border-emerald-500/30">
                      Station
                    </span>
                  ) : (
                    <span className="text-[10px] bg-slate-800 text-slate-400 font-medium px-2 py-0.5 rounded-full">
                      Centroid
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Reset Zoom Button */}
        <button
          onClick={resetToChennai}
          className="pointer-events-auto flex items-center space-x-1.5 px-3 py-2 bg-slate-900/90 backdrop-blur-md border border-slate-700 rounded-2xl text-xs font-semibold text-slate-200 hover:text-white hover:bg-slate-800 transition-all shadow-xl"
        >
          <RotateCcw className="w-3.5 h-3.5 text-sky-400" />
          <span>Reset Chennai</span>
        </button>
      </div>

      {/* Map Canvas */}
      <MapContainer
        center={chennaiCenter}
        zoom={11}
        scrollWheelZoom={true}
        className="w-full h-full flex-1 bg-slate-950 z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        <MapController targetCoords={mapTarget} onMapClick={onMapClick} />

        {/* GCC Wards Boundary Polygons */}
        {showWards && wardsData && (
          <GeoJSON
            data={wardsData}
            style={() => ({
              color: '#6366F1',
              weight: 1.5,
              opacity: 0.6,
              fillColor: '#4338CA',
              fillOpacity: 0.08,
              dashArray: '3'
            })}
            onEachFeature={(feature, layer) => {
              layer.bindPopup(`
                <div style="font-family: sans-serif; color: #0f172a; padding: 4px;">
                  <strong style="font-size: 13px;">${feature.properties.name}</strong>
                  <div style="font-size: 11px; color: #475569; margin-top: 2px;">
                    Administrative Zone • Greater Chennai Corporation
                  </div>
                  <div style="font-size: 10px; color: #64748b; margin-top: 2px;">
                    CRS: ${feature.properties.crs}
                  </div>
                </div>
              `);
            }}
          />
        )}

        {/* Estimated Spatial Grid Cells */}
        {showGrid &&
          gridPoints.map((pt, idx) => (
            <CircleMarker
              key={`grid-${idx}`}
              center={[pt.latitude, pt.longitude]}
              radius={9}
              pathOptions={{
                fillColor: pt.color,
                fillOpacity: 0.45,
                stroke: false
              }}
            >
              <Popup className="custom-leaflet-popup">
                <div className="p-2 text-slate-900 font-sans">
                  <div className="flex items-center space-x-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700">
                      Model Estimate
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      Horizon: {pt.horizon}
                    </span>
                  </div>
                  <div className="mt-1 font-black text-base" style={{ color: pt.color }}>
                    {pt.predicted_aqi !== null ? `${pt.predicted_aqi} AQI` : 'Ineligible'} ({pt.category})
                  </div>
                  <div className="text-xs text-slate-700 font-semibold">
                    Target: {pt.target} = {pt.predicted_pm25} {pt.unit}
                  </div>
                  <div className="text-[11px] text-slate-600 font-mono mt-0.5">
                    95% CI: [{pt.lower_bound_pm25} - {pt.upper_bound_pm25}] {pt.unit}
                  </div>
                  <div className="text-[10px] text-slate-500 italic mt-1">
                    Valid at: {pt.valid_at ? new Date(pt.valid_at).toLocaleString() : 'N/A'}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          ))}

        {/* Hotspots Clusters */}
        {showHotspots &&
          hotspots.map((hs, idx) => (
            <Circle
              key={`hotspot-${idx}`}
              center={[hs.center_latitude, hs.center_longitude]}
              radius={2800}
              pathOptions={{
                fillColor: hs.color,
                fillOpacity: 0.22,
                color: hs.color,
                weight: 2,
                dashArray: '4'
              }}
            >
              <Popup>
                <div className="p-2 text-slate-900 font-sans">
                  <div className="text-xs font-bold text-red-600 uppercase tracking-wider">
                    Pollution Hotspot Cluster #{hs.cluster_id}
                  </div>
                  <div className="font-extrabold text-sm mt-0.5" style={{ color: hs.color }}>
                    Estimated AQI: ~{hs.estimated_aqi} ({hs.severity} Severity)
                  </div>
                  <div className="text-xs text-slate-700">
                    Mean PM2.5: {hs.mean_pm25} µg/m³ across {hs.point_count} cells
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1 italic">
                    Method: {hs.method}
                  </div>
                </div>
              </Popup>
            </Circle>
          ))}

        {/* Ground Monitoring Stations (Authoritative CPCB Monitors) */}
        {showStations &&
          stations.map((st) => (
            <Marker
              key={st.id}
              position={[st.latitude, st.longitude]}
              icon={createStationMarker(st.color)}
            >
              <Popup>
                <div className="p-2.5 text-slate-900 font-sans min-w-[200px]">
                  <div className="flex items-center space-x-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                      Verified Station
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                      {st.freshness.toUpperCase()}
                    </span>
                  </div>
                  <div className="font-bold text-sm text-slate-950 mt-1">
                    {st.name}
                  </div>
                  <div className="text-xs text-slate-600 mb-1.5">
                    Zone: {st.zone_type}
                  </div>
                  <div className="border-t border-slate-200 pt-1.5">
                    <div className="text-base font-extrabold" style={{ color: st.color }}>
                      {st.current_aqi !== null ? `${st.current_aqi} AQI` : 'Insufficient Data'} ({st.category})
                    </div>
                    <div className="text-xs text-slate-700 font-semibold">
                      Current PM2.5: {st.current_pm25} µg/m³
                    </div>
                    {st.dominant_pollutant && (
                      <div className="text-xs text-slate-500">
                        Dominant: {st.dominant_pollutant}
                      </div>
                    )}
                    <div className="text-[10px] text-slate-500 italic mt-1">
                      Observed: {st.last_updated ? new Date(st.last_updated).toLocaleString() : 'N/A'}
                    </div>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}

        {/* Selected Search Locality Pin */}
        {selectedLocality && (
          <Marker
            position={[selectedLocality.latitude, selectedLocality.longitude]}
            icon={createLocalityPin()}
          >
            <Popup>
              <div className="p-2 text-slate-900 font-sans">
                <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-100 text-amber-800">
                  Locality Centroid
                </span>
                <div className="font-bold text-sm mt-1 text-slate-950">
                  {selectedLocality.canonical_name}
                </div>
                <div className="text-xs text-slate-600">
                  {selectedLocality.zone} • {selectedLocality.type}
                </div>
                <div className="mt-1.5 text-[11px] text-amber-900 bg-amber-50 p-1.5 rounded border border-amber-200 leading-tight">
                  {selectedLocality.has_ground_station
                    ? 'Official CAAQMS station operates in this locality.'
                    : 'No ground station located directly at this centroid. Values here represent spatial model forecasts.'}
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Selected Map Click Coordinate Pin */}
        {selectedLocation && (
          <CircleMarker
            center={[selectedLocation.latitude, selectedLocation.longitude]}
            radius={8}
            pathOptions={{ fillColor: '#38BDF8', fillOpacity: 0.9, color: '#FFFFFF', weight: 2 }}
          >
            <Popup>
              <div className="p-1 text-slate-900 font-sans text-xs">
                <strong>Selected Coordinate</strong>
                <div>{selectedLocation.latitude.toFixed(4)}°N, {selectedLocation.longitude.toFixed(4)}°E</div>
              </div>
            </Popup>
          </CircleMarker>
        )}

        {showSatelliteOverlay && (
          <Circle
            center={chennaiCenter}
            radius={25000}
            pathOptions={{ fillColor: '#6366F1', fillOpacity: 0.05, stroke: false }}
          />
        )}
      </MapContainer>

      {/* Floating Bottom Legend */}
      <div className="absolute bottom-4 left-4 right-4 z-[1000] bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-2xl p-3 shadow-xl pointer-events-auto flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center space-x-3 text-slate-300">
          <span className="font-bold text-white text-xs">Legend:</span>
          <span className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500 border border-white inline-block"></span>
            <span>Station Observation</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded bg-amber-500 border border-white rotate-45 inline-block"></span>
            <span>Locality Centroid</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-indigo-500/50 inline-block"></span>
            <span>Model Estimated Grid</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full border border-red-500 border-dashed inline-block"></span>
            <span>Hotspot Cluster</span>
          </span>
        </div>

        <div className="text-[11px] text-slate-400">
          CRS: <span className="text-indigo-300 font-mono">EPSG:4326 (WGS84)</span>
        </div>
      </div>
    </div>
  );
};
