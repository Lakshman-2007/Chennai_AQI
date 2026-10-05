import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, CircleMarker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import type { StationInfo, PredictionPoint, HotspotInfo } from '../types/api';

const createCustomMarker = (color: string) => {
  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `<div style="background-color: ${color}; width: 18px; height: 18px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px ${color};"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9]
  });
};

interface ChennaiMapProps {
  stations?: StationInfo[];
  gridPoints?: PredictionPoint[];
  hotspots?: HotspotInfo[];
  showGrid?: boolean;
  showHotspots?: boolean;
  onMapClick?: (lat: number, lon: number) => void;
  selectedLocation?: { latitude: number; longitude: number } | null;
}

const MapClickHandler: React.FC<{ onMapClick?: (lat: number, lon: number) => void }> = ({ onMapClick }) => {
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
  onMapClick,
  selectedLocation
}) => {
  const chennaiCenter: [number, number] = [13.0427, 80.2407];

  return (
    <div className="w-full h-full min-h-[480px] rounded-2xl overflow-hidden border border-slate-800 shadow-2xl relative">
      <MapContainer
        center={chennaiCenter}
        zoom={11}
        scrollWheelZoom={true}
        className="w-full h-full bg-slate-950 z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        <MapClickHandler onMapClick={onMapClick} />

        {showGrid &&
          gridPoints.map((pt, idx) => (
            <CircleMarker
              key={`grid-${idx}`}
              center={[pt.latitude, pt.longitude]}
              radius={10}
              pathOptions={{
                fillColor: pt.color,
                fillOpacity: 0.45,
                stroke: false
              }}
            >
              <Popup className="custom-leaflet-popup">
                <div className="p-2 text-slate-900 font-sans">
                  <div className="font-bold text-sm">Predicted Location</div>
                  <div className="text-xs text-slate-600">
                    Lat: {pt.latitude.toFixed(4)}, Lon: {pt.longitude.toFixed(4)}
                  </div>
                  <div className="mt-1 font-extrabold text-base" style={{ color: pt.color }}>
                    {pt.predicted_aqi} AQI ({pt.category})
                  </div>
                  <div className="text-xs text-slate-700 font-medium">
                    PM2.5: {pt.predicted_pm25} µg/m³
                  </div>
                  <div className="text-[11px] text-slate-500 italic">
                    95% CI: [{pt.lower_bound_pm25} - {pt.upper_bound_pm25}] µg/m³
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          ))}

        {showHotspots &&
          hotspots.map((hs, idx) => (
            <Circle
              key={`hotspot-${idx}`}
              center={[hs.center_latitude, hs.center_longitude]}
              radius={3000}
              pathOptions={{
                color: hs.color,
                fillColor: hs.color,
                fillOpacity: 0.25,
                weight: 2,
                dashArray: '4, 4'
              }}
            >
              <Popup>
                <div className="p-2 text-slate-900">
                  <span className="text-xs font-bold text-red-600 uppercase tracking-wide">
                    HOTSPOT DETECTED
                  </span>
                  <div className="font-bold text-sm">{hs.location_name}</div>
                  <div className="text-xs font-semibold mt-1" style={{ color: hs.color }}>
                    Mean AQI: {hs.mean_predicted_aqi} ({hs.category})
                  </div>
                  <div className="text-xs text-slate-700">Peak PM2.5: {hs.peak_pm25} µg/m³</div>
                  <div className="text-[11px] text-slate-600 mt-1">{hs.advisory}</div>
                </div>
              </Popup>
            </Circle>
          ))}

        {stations.map((st) => (
          <Marker
            key={st.id}
            position={[st.latitude, st.longitude]}
            icon={createCustomMarker(st.color)}
          >
            <Popup>
              <div className="p-2 text-slate-900 font-sans">
                <div className="font-bold text-sm">{st.name}</div>
                <div className="text-xs text-slate-500 font-medium">{st.zone_type}</div>
                <div className="mt-2 text-lg font-black" style={{ color: st.color }}>
                  {st.current_aqi} AQI ({st.category})
                </div>
                <div className="text-xs font-semibold text-slate-700">
                  PM2.5: {st.current_pm25} µg/m³
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {selectedLocation && (
          <CircleMarker
            center={[selectedLocation.latitude, selectedLocation.longitude]}
            radius={12}
            pathOptions={{
              color: '#38BDF8',
              fillColor: '#0284C7',
              fillOpacity: 0.8,
              weight: 3
            }}
          />
        )}
      </MapContainer>

      <div className="absolute bottom-4 right-4 bg-slate-900/90 backdrop-blur-md border border-slate-800 p-3 rounded-xl z-10 text-xs shadow-xl">
        <span className="font-bold text-slate-300 block mb-2 uppercase tracking-wider text-[10px]">
          CPCB AQI Categories
        </span>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px]">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]"></span>
            <span className="text-slate-300">Good (0-50)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#84CC16]"></span>
            <span className="text-slate-300">Satisfactory (51-100)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]"></span>
            <span className="text-slate-300">Moderate (101-200)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444]"></span>
            <span className="text-slate-300">Poor (201-300)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#9333EA]"></span>
            <span className="text-slate-300">Very Poor (301-400)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#7F1D1D]"></span>
            <span className="text-slate-300">Severe (401-500)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
