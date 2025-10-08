import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

const FRAFrequencyPlot = ({ 
  fraData, 
  baselineData = null, 
  anomalyBands = [], 
  selectedPhasePair = 'H1-H2',
  showMagnitude = true,
  showPhase = true,
  height = 600 
}) => {
  const plotData = useMemo(() => {
    if (!fraData || !fraData.measurement || !fraData.measurement.frequencies) {
      return [];
    }

    const frequencies = fraData.measurement.frequencies;
    const data = [];

    if (showMagnitude) {
      // FRA Magnitude Plot
      const magnitudeTrace = {
        x: frequencies,
        y: fraData.measurement.magnitude || fraData.measurement.response_magnitude,
        type: 'scatter',
        mode: 'lines',
        name: `Magnitude - ${selectedPhasePair}`,
        line: {
          color: '#2563eb',
          width: 2
        },
        yaxis: 'y1'
      };
      data.push(magnitudeTrace);

      // Baseline overlay if available
      if (baselineData && baselineData.magnitude) {
        const baselineTrace = {
          x: frequencies,
          y: baselineData.magnitude,
          type: 'scatter',
          mode: 'lines',
          name: 'Baseline Magnitude',
          line: {
            color: '#16a34a',
            width: 2,
            dash: 'dash'
          },
          yaxis: 'y1'
        };
        data.push(baselineTrace);
      }
    }

    if (showPhase) {
      // FRA Phase Plot
      const phaseTrace = {
        x: frequencies,
        y: fraData.measurement.phase || fraData.measurement.response_phase,
        type: 'scatter',
        mode: 'lines',
        name: `Phase - ${selectedPhasePair}`,
        line: {
          color: '#dc2626',
          width: 2
        },
        yaxis: showMagnitude ? 'y2' : 'y1'
      };
      data.push(phaseTrace);

      // Baseline phase overlay if available
      if (baselineData && baselineData.phase) {
        const baselinePhaseTrace = {
          x: frequencies,
          y: baselineData.phase,
          type: 'scatter',
          mode: 'lines',
          name: 'Baseline Phase',
          line: {
            color: '#059669',
            width: 2,
            dash: 'dash'
          },
          yaxis: showMagnitude ? 'y2' : 'y1'
        };
        data.push(baselinePhaseTrace);
      }
    }

    // Add anomaly band highlights
    anomalyBands.forEach((band, index) => {
      if (band.freq_start && band.freq_end) {
        // Create shaded region for anomaly
        const anomalyTrace = {
          x: [band.freq_start, band.freq_end, band.freq_end, band.freq_start, band.freq_start],
          y: [
            Math.min(...(fraData.measurement.magnitude || fraData.measurement.response_magnitude || [0])),
            Math.min(...(fraData.measurement.magnitude || fraData.measurement.response_magnitude || [0])),
            Math.max(...(fraData.measurement.magnitude || fraData.measurement.response_magnitude || [0])),
            Math.max(...(fraData.measurement.magnitude || fraData.measurement.response_magnitude || [0])),
            Math.min(...(fraData.measurement.magnitude || fraData.measurement.response_magnitude || [0]))
          ],
          fill: 'toself',
          fillcolor: 'rgba(239, 68, 68, 0.2)',
          line: { color: 'rgba(239, 68, 68, 0.5)', width: 1 },
          name: `Anomaly Band ${index + 1}`,
          showlegend: true,
          yaxis: 'y1',
          hovertemplate: `<b>Anomaly Band ${index + 1}</b><br>` +
                        `Frequency: ${(band.freq_start/1e6).toFixed(2)} - ${(band.freq_end/1e6).toFixed(2)} MHz<br>` +
                        `Severity: ${band.severity || 'Unknown'}<br>` +
                        `<extra></extra>`
        };
        data.push(anomalyTrace);
      }
    });

    return data;
  }, [fraData, baselineData, anomalyBands, selectedPhasePair, showMagnitude, showPhase]);

  const layout = useMemo(() => {
    const baseLayout = {
      title: {
        text: `FRA Frequency Response - ${selectedPhasePair}`,
        font: { size: 18, color: '#1f2937' }
      },
      xaxis: {
        title: {
          text: 'Frequency (Hz)',
          font: { size: 14, color: '#374151' }
        },
        type: 'log',
        showgrid: true,
        gridcolor: '#e5e7eb',
        zeroline: false,
        tickformat: '.0s'
      },
      showlegend: true,
      legend: {
        x: 1.02,
        y: 1,
        bgcolor: 'rgba(255, 255, 255, 0.8)',
        bordercolor: '#d1d5db',
        borderwidth: 1
      },
      margin: { l: 80, r: 120, t: 80, b: 80 },
      height: height,
      hovermode: 'x unified',
      plot_bgcolor: '#ffffff',
      paper_bgcolor: '#ffffff'
    };

    if (showMagnitude && showPhase) {
      // Dual y-axis layout
      return {
        ...baseLayout,
        yaxis: {
          title: {
            text: 'Magnitude (dB)',
            font: { size: 14, color: '#2563eb' }
          },
          side: 'left',
          showgrid: true,
          gridcolor: '#e5e7eb',
          zeroline: true,
          zerolinecolor: '#9ca3af'
        },
        yaxis2: {
          title: {
            text: 'Phase (degrees)',
            font: { size: 14, color: '#dc2626' }
          },
          side: 'right',
          overlaying: 'y',
          showgrid: false,
          zeroline: true,
          zerolinecolor: '#f87171'
        }
      };
    } else if (showMagnitude) {
      return {
        ...baseLayout,
        yaxis: {
          title: {
            text: 'Magnitude (dB)',
            font: { size: 14, color: '#2563eb' }
          },
          showgrid: true,
          gridcolor: '#e5e7eb',
          zeroline: true,
          zerolinecolor: '#9ca3af'
        }
      };
    } else {
      return {
        ...baseLayout,
        yaxis: {
          title: {
            text: 'Phase (degrees)',
            font: { size: 14, color: '#dc2626' }
          },
          showgrid: true,
          gridcolor: '#e5e7eb',
          zeroline: true,
          zerolinecolor: '#f87171'
        }
      };
    }
  }, [selectedPhasePair, showMagnitude, showPhase, height]);

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d'],
    displaylogo: false,
    toImageButtonOptions: {
      format: 'png',
      filename: `FRA_plot_${selectedPhasePair}_${new Date().toISOString().split('T')[0]}`,
      height: 800,
      width: 1200,
      scale: 2
    }
  };

  if (!fraData || !fraData.measurement) {
    return (
      <div className="flex items-center justify-center h-96 border border-gray-200 rounded-lg bg-gray-50">
        <div className="text-center">
          <div className="text-gray-500 mb-2">
            <svg className="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">No FRA Data</h3>
          <p className="text-gray-500">Upload FRA data to see frequency response plots</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">FRA Frequency Response</h3>
            <p className="text-sm text-gray-600">Interactive frequency domain analysis</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={showMagnitude}
                  readOnly
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Magnitude</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={showPhase}
                  readOnly
                  className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                />
                <span className="ml-2 text-sm text-gray-700">Phase</span>
              </label>
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

export default FRAFrequencyPlot;