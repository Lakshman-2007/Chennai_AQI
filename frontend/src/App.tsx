import { useState } from 'react';
import { Navbar } from './components/Navbar';
import { OverviewDashboard } from './pages/OverviewDashboard';
import { InteractiveMapPage } from './pages/InteractiveMapPage';
import { TrendAnalyticsPage } from './pages/TrendAnalyticsPage';
import { PredictionsPage } from './pages/PredictionsPage';
import { ExplainabilityPage } from './pages/ExplainabilityPage';
import { ModelPerformancePage } from './pages/ModelPerformancePage';
import { DataSourcesPage } from './pages/DataSourcesPage';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('overview');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      
      {/* Top Navigation */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && <OverviewDashboard onNavigateMap={() => setActiveTab('map')} />}
        {activeTab === 'map' && <InteractiveMapPage />}
        {activeTab === 'trends' && <TrendAnalyticsPage />}
        {activeTab === 'predictions' && <PredictionsPage />}
        {activeTab === 'xai' && <ExplainabilityPage />}
        {activeTab === 'model' && <ModelPerformancePage />}
        {activeTab === 'sources' && <DataSourcesPage />}
      </main>

      {/* Scientific Footer */}
      <footer className="bg-slate-900/80 border-t border-slate-800 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            Hybrid Explainable Multi-Source Air Quality Prediction Framework — Chennai, Tamil Nadu, India
          </span>
          <span className="text-slate-400 font-semibold">
            Sentinel-5P Satellite TROPOMI + Ground Stations + Open-Meteo Weather + Stacking ML
          </span>
        </div>
      </footer>

    </div>
  );
}

export default App;
