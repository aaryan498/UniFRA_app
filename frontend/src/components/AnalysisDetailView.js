import React, { useState, useEffect, useMemo, useCallback } from 'react';
import axios from 'axios';

// Import visualization components
import FRAFrequencyPlot from './visualizations/FRAFrequencyPlot';
import FaultProbabilityChart from './visualizations/FaultProbabilityChart';
import AnomalyHeatmap from './visualizations/AnomalyHeatmap';
import ExplainabilityPlot from './visualizations/ExplainabilityPlot';
import ExportModal from './export/ExportModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AnalysisDetailView = ({ analysisId, onClose }) => {
  const [analysisData, setAnalysisData] = useState(null);
  const [fraData, setFraData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [selectedPhasePair, setSelectedPhasePair] = useState('H1-H2');

  useEffect(() => {
    if (analysisId) {
      loadAnalysisData();
    }
  }, [analysisId]);

  const loadAnalysisData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/analysis/${analysisId}`);
      setAnalysisData(response.data);
      
      // Generate sample FRA data for visualization
      generateSampleFRAData(response.data);
    } catch (error) {
      console.error('Failed to load analysis data:', error);
      setError('Failed to load analysis data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const generateSampleFRAData = useCallback((analysis) => {
    // Generate sample FRA data for visualization purposes
    const frequencies = [];
    const magnitude = [];
    const phase = [];
    
    // Generate logarithmic frequency sweep from 10 Hz to 10 MHz
    const startFreq = 10;
    const endFreq = 10e6;
    const numPoints = 1000;
    const logStart = Math.log10(startFreq);
    const logEnd = Math.log10(endFreq);
    const logStep = (logEnd - logStart) / (numPoints - 1);
    
    for (let i = 0; i < numPoints; i++) {
      const freq = Math.pow(10, logStart + i * logStep);
      frequencies.push(freq);
      
      // Generate realistic FRA magnitude response
      let mag = -20 * Math.log10(freq / 1000) - Math.random() * 5;
      
      // Add fault characteristics based on analysis
      if (analysis.predicted_fault_type !== 'healthy') {
        // Add anomalies in specific frequency ranges
        if (freq > 100000 && freq < 1000000) {
          mag += Math.sin(freq / 100000) * 10 * (1 - analysis.confidence_score);
        }
        if (freq > 50000 && freq < 200000 && analysis.predicted_fault_type === 'axial_displacement') {
          mag -= 15;
        }
      }
      
      magnitude.push(mag);
      
      // Generate phase response
      let ph = -90 * Math.log10(freq / 1000) + Math.random() * 10;
      if (analysis.predicted_fault_type !== 'healthy') {
        ph += Math.cos(freq / 500000) * 20 * (1 - analysis.confidence_score);
      }
      phase.push(ph);
    }

    const sampleFRAData = {
      asset_metadata: analysis.asset_metadata,
      measurement: {
        frequencies,
        magnitude,
        phase,
        freq_start: startFreq,
        freq_end: endFreq,
        unit: 'Hz'
      },
      test_info: {
        test_date: analysis.analysis_timestamp,
        phase_pair: selectedPhasePair,
        test_type: 'FRA_SWEEP'
      }
    };

    setFraData(sampleFRAData);
  }, [selectedPhasePair]);

  const formatFaultName = useCallback((faultType) => {
    return faultType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }, []);

  const getSeverityColor = useCallback((severity) => {
    switch (severity) {
      case 'mild': return 'text-green-600 bg-green-100';
      case 'moderate': return 'text-yellow-600 bg-yellow-100';
      case 'severe': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  }, []);

  const getConfidenceColor = useCallback((confidence) => {
    if (confidence > 0.8) return 'text-green-600';
    if (confidence > 0.6) return 'text-yellow-600';
    return 'text-red-600';
  }, []);

  const generateAnomalyBands = useMemo(() => {
    if (!analysisData || analysisData.predicted_fault_type === 'healthy') return [];
    
    // Generate sample anomaly bands based on fault type
    const bands = [];
    if (analysisData.predicted_fault_type === 'axial_displacement') {
      bands.push({
        freq_start: 200000,
        freq_end: 700000,
        severity: 'moderate',
        description: 'Axial displacement signature'
      });
    }
    if (analysisData.predicted_fault_type === 'turn_turn_short') {
      bands.push({
        freq_start: 1000000,
        freq_end: 5000000,
        severity: 'severe',
        description: 'High frequency anomaly'
      });
    }
    return bands;
  }, [analysisData]);

  const shapData = useMemo(() => {
    // Generate sample SHAP values for demonstration
    const features = [
      'Low Frequency Energy',
      'High Frequency Energy', 
      'Spectral Centroid',
      'Peak Frequency',
      'Bandwidth',
      'Magnitude Variance',
      'Phase Coherence',
      'Harmonic Distortion'
    ];
    
    const shapValues = features.map(() => (Math.random() - 0.5) * 0.6);
    return { features, shapValues };
  }, []);

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 bg-white flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="loading-spinner mb-4"></div>
          <p className="text-sm sm:text-base text-gray-600">Loading analysis details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 z-50 bg-white flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="text-red-500 mb-4">
            <svg className="w-12 h-12 sm:w-16 sm:h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-base sm:text-lg font-medium text-gray-900 mb-2">Error Loading Analysis</h3>
          <p className="text-sm sm:text-base text-gray-600 mb-4">{error}</p>
          <button 
            onClick={onClose}
            className="btn btn-primary px-4 py-2 text-sm sm:text-base"
            data-testid="close-error-view"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'fra-analysis', label: 'FRA Analysis' },
    { id: 'fault-detection', label: 'Fault Detection' },
    { id: 'explainability', label: 'ML Explainability' },
    { id: 'anomalies', label: 'Anomaly Analysis' }
  ];

  return (
    <div className="fixed inset-0 z-50 bg-white overflow-hidden flex flex-col">
      {/* Header - Fully Responsive with improved mobile layout */}
      <div className="bg-white border-b border-gray-200 shadow-sm flex-shrink-0">
        <div className="px-3 sm:px-4 md:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between gap-2 sm:gap-4">
            {/* Left: Close Button + Title */}
            <div className="flex items-center gap-2 sm:gap-3 flex-1 min-w-0">
              <button 
                onClick={onClose}
                className="p-1.5 sm:p-2 hover:bg-gray-100 rounded-lg flex-shrink-0 transition-all duration-200 active:scale-95"
                data-testid="close-detail-view"
                aria-label="Close"
              >
                <svg className="w-5 h-5 sm:w-6 sm:h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <div className="flex-1 min-w-0">
                <h1 className="text-sm sm:text-lg md:text-xl lg:text-2xl font-bold text-gray-900 truncate" data-testid="analysis-detail-title">
                  <span className="hidden sm:inline">Analysis - </span>{analysisData?.asset_metadata?.asset_id || 'N/A'}
                </h1>
                <p className="text-xs sm:text-sm text-gray-600 truncate mt-0.5">
                  {analysisData?.analysis_timestamp ? new Date(analysisData.analysis_timestamp).toLocaleString() : ''}
                </p>
              </div>
            </div>
            
            {/* Right: Export Button - improved responsiveness */}
            <button
              onClick={() => setExportModalOpen(true)}
              className="px-3 py-2 sm:px-4 sm:py-2.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs sm:text-sm font-medium rounded-lg transition-all duration-200 flex items-center gap-1.5 sm:gap-2 flex-shrink-0 shadow-sm hover:shadow-md active:scale-95"
              data-testid="export-analysis-btn"
            >
              <svg className="w-4 h-4 sm:w-4.5 sm:h-4.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>Export</span>
            </button>
          </div>
        </div>

        {/* Tab Navigation - Fully Responsive with better scrolling */}
        <div className="overflow-x-auto scrollbar-hide border-t border-gray-100">
          <nav className="flex px-3 sm:px-4 md:px-6 min-w-max">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 sm:py-3.5 px-3 sm:px-4 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap transition-all duration-200 ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 bg-blue-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                }`}
                data-testid={`tab-${tab.id}`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content Area - Optimized for performance and responsiveness */}
      <div className="flex-1 overflow-y-auto bg-gray-50" style={{ WebkitOverflowScrolling: 'touch' }}>
        <div className="p-3 sm:p-4 md:p-5 lg:p-6">
          {activeTab === 'overview' && (
            <div className="space-y-4 sm:space-y-5 md:space-y-6">
              {/* Summary Cards - Fully Responsive Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 md:gap-5">
                <div className="card hover:shadow-lg transition-shadow duration-200">
                  <div className="card-header px-4 sm:px-5 py-3 sm:py-3.5 bg-gradient-to-r from-blue-50 to-blue-100">
                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Fault Classification</h3>
                  </div>
                  <div className="card-content px-4 sm:px-5 py-4 sm:py-5">
                    <div className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-900 break-words mb-3" data-testid="fault-classification">
                      {formatFaultName(analysisData?.predicted_fault_type || 'unknown')}
                    </div>
                    <span className={`inline-block px-3 py-1.5 rounded-full text-xs sm:text-sm font-medium ${getSeverityColor(analysisData?.severity_level)}`}>
                      {analysisData?.severity_level || 'Unknown'} Severity
                    </span>
                  </div>
                </div>

                <div className="card hover:shadow-lg transition-shadow duration-200">
                  <div className="card-header px-4 sm:px-5 py-3 sm:py-3.5 bg-gradient-to-r from-green-50 to-green-100">
                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Confidence Score</h3>
                  </div>
                  <div className="card-content px-4 sm:px-5 py-4 sm:py-5">
                    <div className={`text-xl sm:text-2xl md:text-3xl font-bold mb-2 ${getConfidenceColor(analysisData?.confidence_score || 0)}`} data-testid="confidence-score">
                      {analysisData?.confidence_score ? (analysisData.confidence_score * 100).toFixed(1) : '0'}%
                    </div>
                    <p className="text-xs sm:text-sm text-gray-600">
                      ML Model Confidence
                    </p>
                  </div>
                </div>

                <div className="card sm:col-span-2 lg:col-span-1 hover:shadow-lg transition-shadow duration-200">
                  <div className="card-header px-4 sm:px-5 py-3 sm:py-3.5 bg-gradient-to-r from-purple-50 to-purple-100">
                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Anomaly Status</h3>
                  </div>
                  <div className="card-content px-4 sm:px-5 py-4 sm:py-5">
                    <div className={`text-xl sm:text-2xl md:text-3xl font-bold break-words mb-2 ${analysisData?.is_anomaly ? 'text-red-600' : 'text-green-600'}`} data-testid="anomaly-status">
                      {analysisData?.is_anomaly ? 'Anomaly Detected' : 'Normal Operation'}
                    </div>
                    <p className="text-xs sm:text-sm text-gray-600">
                      Score: {analysisData?.anomaly_score?.toFixed(3) || '0.000'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Quick Fault Analysis */}
              <div className="card hover:shadow-lg transition-shadow duration-200">
                <div className="card-header px-4 sm:px-5 py-3 sm:py-3.5">
                  <h3 className="text-sm sm:text-base font-semibold text-gray-900">Quick Fault Analysis</h3>
                </div>
                <div className="card-content p-3 sm:p-4 md:p-5">
                  <div className="w-full overflow-x-auto">
                    <FaultProbabilityChart 
                      faultProbabilities={analysisData?.fault_probabilities}
                      chartType="horizontal"
                      height={250}
                    />
                  </div>
                </div>
              </div>

              {/* Recommendations */}
              <div className="card hover:shadow-lg transition-shadow duration-200">
                <div className="card-header px-4 sm:px-5 py-3 sm:py-3.5">
                  <h3 className="text-sm sm:text-base font-semibold text-gray-900">Maintenance Recommendations</h3>
                </div>
                <div className="card-content px-4 sm:px-5 py-4 sm:py-5">
                  <ul className="space-y-3" data-testid="recommendations-list">
                    {analysisData?.recommended_actions?.map((action, index) => (
                      <li key={index} className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded-lg transition-colors">
                        <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold">
                          {index + 1}
                        </span>
                        <span className="text-sm sm:text-base text-gray-800 flex-1">{action}</span>
                      </li>
                    )) || (
                      <li className="text-sm text-gray-500 text-center py-4">No specific recommendations available.</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'fra-analysis' && fraData && (
            <div className="space-y-4 sm:space-y-5 md:space-y-6">
              {/* Phase Pair Selection */}
              <div className="card hover:shadow-lg transition-shadow duration-200">
                <div className="card-header px-4 sm:px-5 py-3 sm:py-3.5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">FRA Frequency Response Analysis</h3>
                    <select
                      value={selectedPhasePair}
                      onChange={(e) => setSelectedPhasePair(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                      data-testid="phase-pair-selector"
                    >
                      <option value="H1-H2">H1-H2</option>
                      <option value="H2-H3">H2-H3</option>
                      <option value="H1-H3">H1-H3</option>
                      <option value="H1-X1">H1-X1</option>
                      <option value="H2-X2">H2-X2</option>
                      <option value="H3-X3">H3-X3</option>
                    </select>
                  </div>
                </div>
                <div className="card-content p-3 sm:p-4 md:p-5">
                  <div className="w-full overflow-x-auto">
                    <FRAFrequencyPlot 
                      fraData={fraData}
                      anomalyBands={generateAnomalyBands}
                      selectedPhasePair={selectedPhasePair}
                      height={400}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'fault-detection' && (
            <div className="space-y-4 sm:space-y-5 md:space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-5 md:gap-6">
                {/* Bar Chart */}
                <div className="card hover:shadow-lg transition-shadow duration-200">
                  <div className="card-header px-4 sm:px-5 py-3 sm:py-3.5">
                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Fault Probabilities (Bar Chart)</h3>
                  </div>
                  <div className="card-content p-3 sm:p-4 md:p-5">
                    <div className="w-full overflow-x-auto">
                      <FaultProbabilityChart 
                        faultProbabilities={analysisData?.fault_probabilities}
                        chartType="bar"
                        height={350}
                      />
                    </div>
                  </div>
                </div>

                {/* Pie Chart */}
                <div className="card hover:shadow-lg transition-shadow duration-200">
                  <div className="card-header px-4 sm:px-5 py-3 sm:py-3.5">
                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Fault Distribution (Pie Chart)</h3>
                  </div>
                  <div className="card-content p-3 sm:p-4 md:p-5">
                    <div className="w-full overflow-x-auto">
                      <FaultProbabilityChart 
                        faultProbabilities={analysisData?.fault_probabilities}
                        chartType="pie"
                        height={350}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'explainability' && (
            <div className="space-y-4 sm:space-y-5 md:space-y-6">
              <div className="card hover:shadow-lg transition-shadow duration-200">
                <div className="card-header px-4 sm:px-5 py-3 sm:py-3.5">
                  <h3 className="text-sm sm:text-base font-semibold text-gray-900">SHAP Feature Importance Analysis</h3>
                  <p className="text-xs sm:text-sm text-gray-600 mt-1">
                    Understanding how different features contribute to the ML prediction
                  </p>
                </div>
                <div className="card-content p-3 sm:p-4 md:p-5">
                  <div className="w-full overflow-x-auto">
                    <ExplainabilityPlot 
                      shapValues={shapData.shapValues}
                      featureNames={shapData.features}
                      plotType="waterfall"
                      height={400}
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-5 md:gap-6">
                <div className="card hover:shadow-lg transition-shadow duration-200">
                  <div className="card-header px-4 sm:px-5 py-3 sm:py-3.5">
                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Feature Contributions (Bar Plot)</h3>
                  </div>
                  <div className="card-content p-3 sm:p-4 md:p-5">
                    <div className="w-full overflow-x-auto">
                      <ExplainabilityPlot 
                        shapValues={shapData.shapValues}
                        featureNames={shapData.features}
                        plotType="bar"
                        height={300}
                      />
                    </div>
                  </div>
                </div>

                <div className="card hover:shadow-lg transition-shadow duration-200">
                  <div className="card-header px-4 sm:px-5 py-3 sm:py-3.5">
                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Force Plot Analysis</h3>
                  </div>
                  <div className="card-content p-3 sm:p-4 md:p-5">
                    <div className="w-full overflow-x-auto">
                      <ExplainabilityPlot 
                        shapValues={shapData.shapValues}
                        featureNames={shapData.features}
                        plotType="force"
                        height={300}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'anomalies' && fraData && (
            <div className="space-y-4 sm:space-y-5 md:space-y-6">
              <div className="card hover:shadow-lg transition-shadow duration-200">
                <div className="card-header px-4 sm:px-5 py-3 sm:py-3.5">
                  <h3 className="text-sm sm:text-base font-semibold text-gray-900">Frequency Band Anomaly Analysis</h3>
                  <p className="text-xs sm:text-sm text-gray-600 mt-1">
                    Heatmap visualization of anomalous frequency bands over time
                  </p>
                </div>
                <div className="card-content p-3 sm:p-4 md:p-5">
                  <div className="w-full overflow-x-auto">
                    <AnomalyHeatmap 
                      fraData={fraData}
                      height={400}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Export Modal */}
      <ExportModal
        isOpen={exportModalOpen}
        onClose={() => setExportModalOpen(false)}
        analysisData={analysisData}
        fraData={fraData}
        assetId={analysisData?.asset_metadata?.asset_id}
      />
    </div>
  );
};

export default AnalysisDetailView;
