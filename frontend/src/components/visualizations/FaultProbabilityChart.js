import React, { useMemo } from 'react';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-basic-dist-min';
const Plot = createPlotlyComponent(Plotly);

const FaultProbabilityChart = ({ 
  faultProbabilities, 
  severityLevels = {},
  chartType = 'bar', // 'bar', 'pie', 'horizontal'
  height = 400,
  showSeverity = true 
}) => {
  const chartData = useMemo(() => {
    if (!faultProbabilities) return [];

    const faultTypes = Object.keys(faultProbabilities).filter(key => 
      faultProbabilities[key] > 0.001 // Filter out negligible probabilities
    );
    
    const probabilities = faultTypes.map(type => faultProbabilities[type]);
    
    const colors = {
      healthy: '#16a34a',
      axial_displacement: '#dc2626',
      radial_deformation: '#ea580c',
      core_grounding: '#9333ea',
      turn_turn_short: '#c2410c',
      open_circuit: '#991b1b',
      insulation_degradation: '#b91c1c',
      partial_discharge: '#7c2d12',
      lamination_deform: '#a16207',
      saturation_effect: '#166534'
    };

    const formatFaultName = (faultType) => {
      return faultType
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    };

    const getSeverityColor = (severity) => {
      switch (severity) {
        case 'mild': return '#22c55e';
        case 'moderate': return '#f59e0b'; 
        case 'severe': return '#ef4444';
        default: return '#6b7280';
      }
    };

    if (chartType === 'pie') {
      return [{
        values: probabilities,
        labels: faultTypes.map(formatFaultName),
        type: 'pie',
        hole: 0.4,
        marker: {
          colors: faultTypes.map(type => colors[type] || '#6b7280'),
          line: { color: '#ffffff', width: 2 }
        },
        textinfo: 'label+percent',
        textposition: 'auto',
        hovertemplate: '<b>%{label}</b><br>' +
                      'Probability: %{percent}<br>' +
                      'Value: %{value:.3f}<br>' +
                      '<extra></extra>',
        textfont: { size: 11 }
      }];
    }

    if (chartType === 'horizontal') {
      return [{
        y: faultTypes.map(formatFaultName),
        x: probabilities,
        type: 'bar',
        orientation: 'h',
        marker: {
          color: faultTypes.map(type => colors[type] || '#6b7280'),
          line: { color: '#ffffff', width: 1 }
        },
        hovertemplate: '<b>%{y}</b><br>' +
                      'Probability: %{x:.1%}<br>' +
                      '<extra></extra>',
        texttemplate: '%{x:.1%}',
        textposition: 'outside'
      }];
    }

    // Default bar chart
    const traces = [{
      x: faultTypes.map(formatFaultName),
      y: probabilities,
      type: 'bar',
      marker: {
        color: faultTypes.map(type => colors[type] || '#6b7280'),
        line: { color: '#ffffff', width: 1 }
      },
      hovertemplate: '<b>%{x}</b><br>' +
                    'Probability: %{y:.1%}<br>' +
                    '<extra></extra>',
      texttemplate: '%{y:.1%}',
      textposition: 'outside',
      name: 'Fault Probability'
    }];

    // Add severity information if available
    if (showSeverity && severityLevels && Object.keys(severityLevels).length > 0) {
      const severityTrace = {
        x: faultTypes.map(formatFaultName),
        y: faultTypes.map(type => severityLevels[type] === 'mild' ? 0.3 : 
                                severityLevels[type] === 'moderate' ? 0.6 : 
                                severityLevels[type] === 'severe' ? 0.9 : 0),
        type: 'scatter',
        mode: 'markers',
        marker: {
          size: 12,
          color: faultTypes.map(type => getSeverityColor(severityLevels[type])),
          symbol: 'diamond',
          line: { color: '#ffffff', width: 2 }
        },
        yaxis: 'y2',
        name: 'Severity Level',
        hovertemplate: '<b>%{x}</b><br>' +
                      'Severity: ' + faultTypes.map(type => severityLevels[type] || 'Unknown').join('<br>Severity: ') +
                      '<extra></extra>'
      };
      traces.push(severityTrace);
    }

    return traces;
  }, [faultProbabilities, severityLevels, chartType, showSeverity]);

  const layout = useMemo(() => {
    const baseLayout = {
      title: {
        text: 'Fault Classification Results',
        font: { size: 16, color: '#1f2937' },
        y: 0.95
      },
      showlegend: chartType !== 'pie',
      legend: {
        x: 1.02,
        y: 1,
        bgcolor: 'rgba(255, 255, 255, 0.8)',
        bordercolor: '#d1d5db',
        borderwidth: 1
      },
      margin: chartType === 'pie' ? 
        { l: 20, r: 20, t: 40, b: 20 } : 
        { l: 60, r: 120, t: 60, b: 100 },
      height: height,
      plot_bgcolor: '#ffffff',
      paper_bgcolor: '#ffffff',
      hovermode: chartType === 'pie' ? 'closest' : 'x'
    };

    if (chartType === 'pie') {
      return {
        ...baseLayout,
        annotations: [{
          text: 'Fault<br>Analysis',
          x: 0.5,
          y: 0.5,
          font: { size: 14, color: '#374151' },
          showarrow: false
        }]
      };
    }

    if (chartType === 'horizontal') {
      return {
        ...baseLayout,
        xaxis: {
          title: { text: 'Probability', font: { size: 12 } },
          tickformat: '.1%',
          showgrid: true,
          gridcolor: '#e5e7eb',
          zeroline: true,
          zerolinecolor: '#9ca3af'
        },
        yaxis: {
          title: { text: 'Fault Type', font: { size: 12 } },
          showgrid: false,
          categoryorder: 'total ascending'
        }
      };
    }

    // Default bar chart layout
    const layout = {
      ...baseLayout,
      xaxis: {
        title: { text: 'Fault Type', font: { size: 12 } },
        showgrid: false,
        tickangle: -45
      },
      yaxis: {
        title: { text: 'Probability', font: { size: 12 } },
        tickformat: '.1%',
        showgrid: true,
        gridcolor: '#e5e7eb',
        zeroline: true,
        zerolinecolor: '#9ca3af',
        range: [0, 1]
      }
    };

    if (showSeverity && severityLevels && Object.keys(severityLevels).length > 0) {
      layout.yaxis2 = {
        title: { text: 'Severity', font: { size: 12, color: '#dc2626' } },
        side: 'right',
        overlaying: 'y',
        showgrid: false,
        tickvals: [0.3, 0.6, 0.9],
        ticktext: ['Mild', 'Moderate', 'Severe'],
        range: [0, 1]
      };
    }

    return layout;
  }, [chartType, height, showSeverity, severityLevels]);

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'autoScale2d'],
    displaylogo: false,
    toImageButtonOptions: {
      format: 'png',
      filename: `fault_analysis_${chartType}_${new Date().toISOString().split('T')[0]}`,
      height: 600,
      width: 800,
      scale: 2
    }
  };

  if (!faultProbabilities || Object.keys(faultProbabilities).length === 0) {
    return (
      <div className="flex items-center justify-center h-64 border border-gray-200 rounded-lg bg-gray-50">
        <div className="text-center">
          <div className="text-gray-500 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clipRule="evenodd" />
              <path fillRule="evenodd" d="M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm2.5 7a1.5 1.5 0 100-3 1.5 1.5 0 000 3zm2.45 4a2.5 2.5 0 10-4.9 0h4.9zM12 9a1 1 0 100 2h3a1 1 0 100-2h-3zm-1 4a1 1 0 011-1h2a1 1 0 110 2h-2a1 1 0 01-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">No Analysis Data</h3>
          <p className="text-gray-500">Run FRA analysis to see fault probabilities</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Fault Analysis Results</h3>
            <p className="text-sm text-gray-600">AI-powered fault classification and severity assessment</p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              ML Confidence: {Math.max(...Object.values(faultProbabilities)).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
      <div className="p-4">
        <Plot
          data={chartData}
          layout={layout}
          config={config}
          style={{ width: '100%', height: `${height}px` }}
          useResizeHandler={true}
        />
      </div>
    </div>
  );
};

export default FaultProbabilityChart;