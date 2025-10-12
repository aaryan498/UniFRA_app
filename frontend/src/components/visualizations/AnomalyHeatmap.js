import React, { useMemo } from 'react';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-basic-dist-min';
const Plot = createPlotlyComponent(Plotly);

const AnomalyHeatmap = ({ 
  fraData, 
  anomalyScores = [],
  frequencyBands = [],
  threshold = 0.05,
  height = 400 
}) => {
  const heatmapData = useMemo(() => {
    if (!fraData || !fraData.measurement) return [];

    const frequencies = fraData.measurement.frequencies;
    const magnitude = fraData.measurement.magnitude || fraData.measurement.response_magnitude;
    
    if (!frequencies || !magnitude) return [];

    // Create frequency bands for analysis
    const numBands = 50; // Number of frequency bands
    const logStart = Math.log10(Math.min(...frequencies));
    const logEnd = Math.log10(Math.max(...frequencies));
    const logStep = (logEnd - logStart) / numBands;
    
    const bands = [];
    const bandAnomalyScores = [];
    const bandLabels = [];
    
    for (let i = 0; i < numBands; i++) {
      const freqStart = Math.pow(10, logStart + i * logStep);
      const freqEnd = Math.pow(10, logStart + (i + 1) * logStep);
      
      // Find data points in this band
      const bandIndices = frequencies
        .map((freq, idx) => ({ freq, idx }))
        .filter(item => item.freq >= freqStart && item.freq < freqEnd)
        .map(item => item.idx);
      
      if (bandIndices.length > 0) {
        // Calculate band statistics
        const bandMagnitudes = bandIndices.map(idx => magnitude[idx]);
        const avgMagnitude = bandMagnitudes.reduce((sum, val) => sum + val, 0) / bandMagnitudes.length;
        const stdMagnitude = Math.sqrt(
          bandMagnitudes.reduce((sum, val) => sum + Math.pow(val - avgMagnitude, 2), 0) / bandMagnitudes.length
        );
        
        // Calculate anomaly score based on deviation from expected
        // Higher deviation = higher anomaly score
        const normalizedStd = Math.min(stdMagnitude / 10, 1); // Normalize to 0-1 range
        const anomalyScore = normalizedStd;
        
        bands.push({
          freqStart,
          freqEnd,
          centerFreq: Math.sqrt(freqStart * freqEnd),
          avgMagnitude,
          stdMagnitude,
          anomalyScore
        });
        
        bandAnomalyScores.push(anomalyScore);
        bandLabels.push(`${(freqStart/1e6).toFixed(2)}-${(freqEnd/1e6).toFixed(2)} MHz`);
      }
    }

    // Create 2D heatmap data
    const timeSteps = 10; // Simulated time steps for demonstration
    const heatmapZ = [];
    const timeLabels = [];
    
    for (let t = 0; t < timeSteps; t++) {
      const timeLabel = `T${t + 1}`;
      timeLabels.push(timeLabel);
      
      // Add some time-based variation to anomaly scores
      const timeVariation = Math.sin(t * Math.PI / timeSteps) * 0.2;
      const rowData = bandAnomalyScores.map(score => 
        Math.max(0, Math.min(1, score + timeVariation + (Math.random() - 0.5) * 0.1))
      );
      heatmapZ.push(rowData);
    }

    return [{
      z: heatmapZ,
      x: bandLabels,
      y: timeLabels,
      type: 'heatmap',
      colorscale: [
        [0, '#16a34a'],     // Green for normal
        [0.3, '#eab308'],   // Yellow for mild anomaly
        [0.6, '#f97316'],   // Orange for moderate anomaly
        [1, '#dc2626']      // Red for severe anomaly
      ],
      showscale: true,
      colorbar: {
        title: {
          text: 'Anomaly Score',
          font: { size: 12 }
        },
        tickvals: [0, 0.25, 0.5, 0.75, 1.0],
        ticktext: ['Normal', 'Low', 'Medium', 'High', 'Critical']
      },
      hovertemplate: '<b>Frequency Band: %{x}</b><br>' +
                    'Time: %{y}<br>' +
                    'Anomaly Score: %{z:.3f}<br>' +
                    '<extra></extra>',
      zmin: 0,
      zmax: 1
    }];
  }, [fraData, anomalyScores, frequencyBands]);

  const layout = useMemo(() => ({
    title: {
      text: 'Frequency Band Anomaly Analysis',
      font: { size: 16, color: '#1f2937' }
    },
    xaxis: {
      title: {
        text: 'Frequency Bands (MHz)',
        font: { size: 12 }
      },
      tickangle: -45,
      showgrid: false
    },
    yaxis: {
      title: {
        text: 'Analysis Timeline',
        font: { size: 12 }
      },
      showgrid: false
    },
    margin: { l: 80, r: 120, t: 60, b: 120 },
    height: height,
    plot_bgcolor: '#ffffff',
    paper_bgcolor: '#ffffff'
  }), [height]);

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d'],
    displaylogo: false,
    toImageButtonOptions: {
      format: 'png',
      filename: `anomaly_heatmap_${new Date().toISOString().split('T')[0]}`,
      height: 600,
      width: 1000,
      scale: 2
    }
  };

  if (!fraData || !fraData.measurement) {
    return (
      <div className="flex items-center justify-center h-64 border border-gray-200 rounded-lg bg-gray-50">
        <div className="text-center">
          <div className="text-gray-500 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">No Anomaly Data</h3>
          <p className="text-gray-500">Run analysis to see frequency band anomalies</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Anomaly Localization</h3>
            <p className="text-sm text-gray-600">Frequency band energy and deviation analysis</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 rounded bg-green-500"></div>
              <span className="text-xs text-gray-600">Normal</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 rounded bg-yellow-500"></div>
              <span className="text-xs text-gray-600">Mild</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 rounded bg-orange-500"></div>
              <span className="text-xs text-gray-600">Moderate</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 rounded bg-red-500"></div>
              <span className="text-xs text-gray-600">Critical</span>
            </div>
          </div>
        </div>
      </div>
      <div className="p-4">
        <Plot
          data={heatmapData}
          layout={layout}
          config={config}
          style={{ width: '100%', height: `${height}px` }}
          useResizeHandler={true}
        />
      </div>
    </div>
  );
};

export default AnomalyHeatmap;