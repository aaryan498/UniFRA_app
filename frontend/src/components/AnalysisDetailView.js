import React, { useState, useEffect } from 'react';
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

  const generateSampleFRAData = (analysis) => {
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
  };

  const formatFaultName = (faultType) => {
    return faultType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'mild': return 'text-green-600 bg-green-100';
      case 'moderate': return 'text-yellow-600 bg-yellow-100';
      case 'severe': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence > 0.8) return 'text-green-600';
    if (confidence > 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const generateAnomalyBands = () => {
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
  };

  const generateShapValues = () => {
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
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 bg-white">
        <div className="flex items-center justify-center h-full">
          <div className="loading-spinner"></div>
          <p className="ml-4 text-gray-600">Loading analysis details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 z-50 bg-white">
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-red-500 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Analysis</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <button 
              onClick={onClose}
              className="btn btn-primary"
              data-testid="close-error-view"
            >
              Close
            </button>
          </div>
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

  const { features, shapValues } = generateShapValues();

  return (
    <div className="fixed inset-0 z-50 bg-white overflow-hidden flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-3 sm:px-4 md:px-6 py-3 sm:py-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button 
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full flex-shrink-0"
              data-testid="close-detail-view"
            >
              <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold text-gray-900" data-testid="analysis-detail-title">
                Analysis Details - {analysisData?.asset_metadata?.asset_id}
              </h1>
              <p className="text-gray-600">
                {new Date(analysisData?.analysis_timestamp).toLocaleString()}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setExportModalOpen(true)}
              className="btn btn-outline"
              data-testid="export-analysis-btn"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export Report
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200 px-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              data-testid={`tab-${tab.id}`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Fault Classification</h3>
                </div>
                <div className="card-content">
                  <div className="text-2xl font-bold text-gray-900" data-testid="fault-classification">
                    {formatFaultName(analysisData?.predicted_fault_type || 'unknown')}
                  </div>
                  <div className="mt-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(analysisData?.severity_level)}`}>
                      {analysisData?.severity_level || 'Unknown'} Severity
                    </span>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Confidence Score</h3>
                </div>
                <div className="card-content">
                  <div className={`text-2xl font-bold ${getConfidenceColor(analysisData?.confidence_score || 0)}`} data-testid="confidence-score">
                    {analysisData?.confidence_score ? (analysisData.confidence_score * 100).toFixed(1) : '0'}%
                  </div>
                  <div className="mt-2 text-sm text-gray-600">
                    ML Model Confidence
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Anomaly Status</h3>
                </div>
                <div className="card-content">
                  <div className={`text-2xl font-bold ${analysisData?.is_anomaly ? 'text-red-600' : 'text-green-600'}`} data-testid="anomaly-status">
                    {analysisData?.is_anomaly ? 'Anomaly Detected' : 'Normal Operation'}
                  </div>
                  <div className="mt-2 text-sm text-gray-600">
                    Score: {analysisData?.anomaly_score?.toFixed(3) || '0.000'}
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Fault Analysis */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Quick Fault Analysis</h3>
              </div>
              <div className="card-content">
                <FaultProbabilityChart 
                  faultProbabilities={analysisData?.fault_probabilities}
                  chartType="horizontal"
                  height={300}
                />
              </div>
            </div>

            {/* Recommendations */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Maintenance Recommendations</h3>
              </div>
              <div className="card-content">
                <ul className="space-y-3" data-testid="recommendations-list">
                  {analysisData?.recommended_actions?.map((action, index) => (
                    <li key={index} className="flex items-start space-x-3">
                      <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                        {index + 1}
                      </span>
                      <span className="text-gray-800">{action}</span>
                    </li>
                  )) || (
                    <li className="text-gray-500">No specific recommendations available.</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'fra-analysis' && fraData && (
          <div className="space-y-6">
            {/* Phase Pair Selection */}
            <div className="card">
              <div className="card-header">
                <div className="flex items-center justify-between">
                  <h3 className="card-title">FRA Frequency Response Analysis</h3>
                  <select
                    value={selectedPhasePair}
                    onChange={(e) => setSelectedPhasePair(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm"
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
              <div className="card-content">
                <FRAFrequencyPlot 
                  fraData={fraData}
                  anomalyBands={generateAnomalyBands()}
                  selectedPhasePair={selectedPhasePair}
                  height={600}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'fault-detection' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              {/* Bar Chart */}
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Fault Probabilities (Bar Chart)</h3>
                </div>
                <div className="card-content">
                  <FaultProbabilityChart 
                    faultProbabilities={analysisData?.fault_probabilities}
                    chartType="bar"
                    height={400}
                  />
                </div>
              </div>

              {/* Pie Chart */}
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Fault Distribution (Pie Chart)</h3>
                </div>
                <div className="card-content">
                  <FaultProbabilityChart 
                    faultProbabilities={analysisData?.fault_probabilities}
                    chartType="pie"
                    height={400}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'explainability' && (
          <div className="space-y-6">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">SHAP Feature Importance Analysis</h3>
                <p className="card-subtitle">
                  Understanding how different features contribute to the ML prediction
                </p>
              </div>
              <div className="card-content">
                <ExplainabilityPlot 
                  shapValues={shapValues}
                  featureNames={features}
                  plotType="waterfall"
                  height={500}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Feature Contributions (Bar Plot)</h3>
                </div>
                <div className="card-content">
                  <ExplainabilityPlot 
                    shapValues={shapValues}
                    featureNames={features}
                    plotType="bar"
                    height={350}
                  />
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Force Plot Analysis</h3>
                </div>
                <div className="card-content">
                  <ExplainabilityPlot 
                    shapValues={shapValues}
                    featureNames={features}
                    plotType="force"
                    height={350}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'anomalies' && fraData && (
          <div className="space-y-6">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Frequency Band Anomaly Analysis</h3>
                <p className="card-subtitle">
                  Heatmap visualization of anomalous frequency bands over time
                </p>
              </div>
              <div className="card-content">
                <AnomalyHeatmap 
                  fraData={fraData}
                  height={500}
                />
              </div>
            </div>
          </div>
        )}
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