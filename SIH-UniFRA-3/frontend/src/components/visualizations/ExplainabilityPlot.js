import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

const ExplainabilityPlot = ({ 
  shapValues = [], 
  featureNames = [], 
  baseValue = 0,
  plotType = 'waterfall', // 'waterfall', 'bar', 'force'
  height = 400 
}) => {
  const plotData = useMemo(() => {
    if (!shapValues || shapValues.length === 0 || !featureNames || featureNames.length === 0) {
      return [];
    }

    // Create sample SHAP values if not provided
    const sampleShapValues = shapValues.length > 0 ? shapValues : 
      featureNames.map(() => (Math.random() - 0.5) * 0.4);
    
    const sampleFeatureNames = featureNames.length > 0 ? featureNames : [
      'Low Freq Energy', 'High Freq Energy', 'Spectral Centroid', 
      'Peak Frequency', 'Bandwidth', 'Magnitude Variance',
      'Phase Coherence', 'Harmonic Distortion', 'Signal Noise Ratio'
    ].slice(0, sampleShapValues.length);

    if (plotType === 'waterfall') {
      // Create waterfall plot showing cumulative SHAP contributions
      const cumulativeValues = [];
      let cumulative = baseValue;
      cumulativeValues.push(cumulative);
      
      sampleShapValues.forEach(value => {
        cumulative += value;
        cumulativeValues.push(cumulative);
      });

      const traces = [];
      
      // Base value
      traces.push({
        x: ['Base Value'],
        y: [baseValue],
        type: 'bar',
        marker: { color: '#6b7280' },
        name: 'Base Value',
        hovertemplate: '<b>Base Value</b><br>Value: %{y:.3f}<extra></extra>'
      });

      // Feature contributions
      sampleShapValues.forEach((value, index) => {
        traces.push({
          x: [sampleFeatureNames[index]],
          y: [Math.abs(value)],
          base: [cumulativeValues[index] - (value > 0 ? 0 : Math.abs(value))],
          type: 'bar',
          marker: { 
            color: value > 0 ? '#16a34a' : '#dc2626',
            opacity: 0.8
          },
          name: value > 0 ? 'Positive Impact' : 'Negative Impact',
          showlegend: index === 0,
          hovertemplate: `<b>${sampleFeatureNames[index]}</b><br>` +
                        `SHAP Value: ${value > 0 ? '+' : ''}%{base}<br>` +
                        `Impact: ${value > 0 ? 'Increases' : 'Decreases'} prediction<br>` +
                        '<extra></extra>',
          customdata: [value]
        });
      });

      // Final prediction
      traces.push({
        x: ['Final Prediction'],
        y: [cumulativeValues[cumulativeValues.length - 1]],
        type: 'bar',
        marker: { color: '#2563eb' },
        name: 'Final Prediction',
        hovertemplate: '<b>Final Prediction</b><br>Value: %{y:.3f}<extra></extra>'
      });

      return traces;
    }

    if (plotType === 'force') {
      // Create force plot showing positive and negative contributions
      const positiveValues = sampleShapValues.filter(val => val > 0);
      const negativeValues = sampleShapValues.filter(val => val < 0);
      const positiveFeatures = sampleFeatureNames.filter((_, idx) => sampleShapValues[idx] > 0);
      const negativeFeatures = sampleFeatureNames.filter((_, idx) => sampleShapValues[idx] < 0);

      return [
        {
          x: positiveFeatures,
          y: positiveValues,
          type: 'bar',
          marker: { color: '#16a34a', opacity: 0.8 },
          name: 'Positive Contribution',
          hovertemplate: '<b>%{x}</b><br>SHAP Value: +%{y:.3f}<br>Increases prediction<extra></extra>'
        },
        {
          x: negativeFeatures,
          y: negativeValues,
          type: 'bar',
          marker: { color: '#dc2626', opacity: 0.8 },
          name: 'Negative Contribution',
          hovertemplate: '<b>%{x}</b><br>SHAP Value: %{y:.3f}<br>Decreases prediction<extra></extra>'
        }
      ];
    }

    // Default bar plot
    return [{
      x: sampleFeatureNames,
      y: sampleShapValues,
      type: 'bar',
      marker: {
        color: sampleShapValues.map(val => val > 0 ? '#16a34a' : '#dc2626'),
        opacity: 0.8,
        line: { color: '#ffffff', width: 1 }
      },
      hovertemplate: '<b>%{x}</b><br>' +
                    'SHAP Value: %{y:.3f}<br>' +
                    'Impact: ' + sampleShapValues.map(val => val > 0 ? 'Positive' : 'Negative').join('<br>Impact: ') +
                    '<extra></extra>',
      name: 'Feature Importance'
    }];
  }, [shapValues, featureNames, baseValue, plotType]);

  const layout = useMemo(() => {
    const baseLayout = {
      title: {
        text: plotType === 'waterfall' ? 'SHAP Waterfall Plot' : 
              plotType === 'force' ? 'SHAP Force Plot' : 'SHAP Feature Importance',
        font: { size: 16, color: '#1f2937' }
      },
      showlegend: plotType !== 'bar',
      legend: {
        x: 1.02,
        y: 1,
        bgcolor: 'rgba(255, 255, 255, 0.8)',
        bordercolor: '#d1d5db',
        borderwidth: 1
      },
      margin: { l: 60, r: 120, t: 60, b: 120 },
      height: height,
      plot_bgcolor: '#ffffff',
      paper_bgcolor: '#ffffff',
      hovermode: 'x'
    };

    if (plotType === 'waterfall') {
      return {
        ...baseLayout,
        xaxis: {
          title: { text: 'Features', font: { size: 12 } },
          tickangle: -45,
          showgrid: false
        },
        yaxis: {
          title: { text: 'Prediction Value', font: { size: 12 } },
          showgrid: true,
          gridcolor: '#e5e7eb',
          zeroline: true,
          zerolinecolor: '#9ca3af'
        },
        annotations: [{
          x: 0.02,
          y: 0.98,
          xref: 'paper',
          yref: 'paper',
          text: 'Red bars decrease prediction<br>Green bars increase prediction',
          font: { size: 10, color: '#6b7280' },
          showarrow: false,
          bgcolor: 'rgba(255, 255, 255, 0.8)',
          bordercolor: '#d1d5db',
          borderwidth: 1
        }]
      };
    }

    return {
      ...baseLayout,
      xaxis: {
        title: { text: 'Features', font: { size: 12 } },
        tickangle: -45,
        showgrid: false
      },
      yaxis: {
        title: { text: 'SHAP Value', font: { size: 12 } },
        showgrid: true,
        gridcolor: '#e5e7eb',
        zeroline: true,
        zerolinecolor: '#9ca3af'
      }
    };
  }, [plotType, height]);

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d'],
    displaylogo: false,
    toImageButtonOptions: {
      format: 'png',
      filename: `shap_${plotType}_${new Date().toISOString().split('T')[0]}`,
      height: 600,
      width: 1000,
      scale: 2
    }
  };

  if ((!shapValues || shapValues.length === 0) && (!featureNames || featureNames.length === 0)) {
    return (
      <div className="flex items-center justify-center h-64 border border-gray-200 rounded-lg bg-gray-50">
        <div className="text-center">
          <div className="text-gray-500 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">No Explainability Data</h3>
          <p className="text-gray-500">Feature importance analysis will appear here after ML analysis</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">ML Explainability Analysis</h3>
            <p className="text-sm text-gray-600">SHAP values showing feature contribution to prediction</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 rounded bg-green-500"></div>
              <span className="text-xs text-gray-600">Positive Impact</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 rounded bg-red-500"></div>
              <span className="text-xs text-gray-600">Negative Impact</span>
            </div>
          </div>
        </div>
      </div>
      <div className="p-4">
        <Plot
          data={plotData}
          layout={layout}
          config={config}
          style={{ width: '100%', height: `${height}px` }}
          useResizeHandler={true}
        />
      </div>
    </div>
  );
};

export default ExplainabilityPlot;