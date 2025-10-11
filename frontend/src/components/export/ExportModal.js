import React, { useState, useRef } from 'react';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

const ExportModal = ({ 
  isOpen, 
  onClose, 
  analysisData, 
  fraData, 
  assetId 
}) => {
  const [exportFormat, setExportFormat] = useState('pdf');
  const [includeSections, setIncludeSections] = useState({
    summary: true,
    fraPlots: true,
    faultAnalysis: true,
    explainability: true,
    recommendations: true,
    rawData: false
  });
  const [isExporting, setIsExporting] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const reportRef = useRef();

  const handleExport = async () => {
    setIsExporting(true);
    try {
      switch (exportFormat) {
        case 'pdf':
          await exportToPDF();
          break;
        case 'csv':
          await exportToCSV();
          break;
        case 'json':
          await exportToJSON();
          break;
        case 'image':
          await exportToImage();
          break;
        default:
          throw new Error('Unsupported export format');
      }
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const exportToPDF = async () => {
    if (!reportRef.current) return;

    // Create a temporary container for PDF generation
    const pdfContainer = document.createElement('div');
    pdfContainer.style.position = 'absolute';
    pdfContainer.style.left = '-9999px';
    pdfContainer.style.width = '794px'; // A4 width in pixels at 96 DPI
    pdfContainer.style.backgroundColor = '#ffffff';
    pdfContainer.innerHTML = generatePDFContent();
    document.body.appendChild(pdfContainer);

    try {
      const canvas = await html2canvas(pdfContainer, {
        scale: 2,
        useCORS: true,
        logging: false,
        width: 794,
        height: 1123 // A4 height in pixels
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      
      const filename = `FRA_Analysis_${assetId}_${new Date().toISOString().split('T')[0]}.pdf`;
      pdf.save(filename);
    } finally {
      document.body.removeChild(pdfContainer);
    }
  };

  const exportToCSV = async () => {
    const csvData = [];
    
    // Header
    csvData.push(['UniFRA Analysis Export']);
    csvData.push(['Asset ID', assetId]);
    csvData.push(['Analysis Date', new Date(analysisData?.analysis_timestamp).toLocaleString()]);
    csvData.push(['']);

    if (includeSections.faultAnalysis && analysisData?.fault_probabilities) {
      csvData.push(['Fault Analysis']);
      csvData.push(['Fault Type', 'Probability', 'Confidence']);
      Object.entries(analysisData.fault_probabilities).forEach(([fault, probability]) => {
        csvData.push([
          fault.replace('_', ' '),
          (probability * 100).toFixed(2) + '%',
          analysisData.confidence_score ? (analysisData.confidence_score * 100).toFixed(2) + '%' : 'N/A'
        ]);
      });
      csvData.push(['']);
    }

    if (includeSections.recommendations && analysisData?.recommended_actions) {
      csvData.push(['Recommendations']);
      analysisData.recommended_actions.forEach((action, index) => {
        csvData.push([`${index + 1}`, action]);
      });
      csvData.push(['']);
    }

    if (includeSections.rawData && fraData?.measurement) {
      csvData.push(['FRA Measurement Data']);
      csvData.push(['Frequency (Hz)', 'Magnitude (dB)', 'Phase (degrees)']);
      
      const frequencies = fraData.measurement.frequencies || [];
      const magnitude = fraData.measurement.magnitude || fraData.measurement.response_magnitude || [];
      const phase = fraData.measurement.phase || fraData.measurement.response_phase || [];
      
      for (let i = 0; i < Math.min(frequencies.length, magnitude.length); i++) {
        csvData.push([
          frequencies[i],
          magnitude[i] || 'N/A',
          phase[i] || 'N/A'
        ]);
      }
    }

    const csvContent = csvData.map(row => row.map(field => `"${field}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `FRA_Analysis_${assetId}_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const exportToJSON = async () => {
    const jsonData = {
      export_info: {
        export_timestamp: new Date().toISOString(),
        asset_id: assetId,
        format_version: '1.0',
        exported_sections: Object.entries(includeSections)
          .filter(([_, included]) => included)
          .map(([section, _]) => section)
      },
      ...(includeSections.summary && {
        analysis_summary: {
          analysis_id: analysisData?.analysis_id,
          timestamp: analysisData?.analysis_timestamp,
          predicted_fault: analysisData?.predicted_fault_type,
          severity: analysisData?.severity_level,
          confidence: analysisData?.confidence_score,
          is_anomaly: analysisData?.is_anomaly
        }
      }),
      ...(includeSections.faultAnalysis && {
        fault_analysis: {
          probabilities: analysisData?.fault_probabilities,
          anomaly_score: analysisData?.anomaly_score,
          frequency_bands_affected: analysisData?.frequency_bands_affected
        }
      }),
      ...(includeSections.recommendations && {
        maintenance_recommendations: analysisData?.recommended_actions
      }),
      ...(includeSections.rawData && fraData && {
        fra_measurement: {
          asset_metadata: fraData.asset_metadata,
          measurement_data: fraData.measurement,
          test_info: fraData.test_info
        }
      })
    };

    const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `FRA_Analysis_${assetId}_${new Date().toISOString().split('T')[0]}.json`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const exportToImage = async () => {
    if (!reportRef.current) return;

    try {
      const canvas = await html2canvas(reportRef.current, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff'
      });

      const link = document.createElement('a');
      link.download = `FRA_Analysis_${assetId}_${new Date().toISOString().split('T')[0]}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (error) {
      console.error('Image export failed:', error);
    }
  };

  const generatePDFContent = () => {
    return `
      <div style="padding: 20px; font-family: Arial, sans-serif; line-height: 1.4;">
        <!-- Header -->
        <div style="text-align: center; border-bottom: 2px solid #2563eb; padding-bottom: 15px; margin-bottom: 20px;">
          <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
            <svg width="40" height="40" fill="#2563eb" viewBox="0 0 24 24" style="margin-right: 10px;">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
            <h1 style="color: #2563eb; margin: 0; font-size: 24px;">UniFRA</h1>
          </div>
          <h2 style="color: #1f2937; margin: 0; font-size: 18px;">FRA Analysis Report</h2>
          <p style="color: #6b7280; margin: 5px 0 0 0; font-size: 12px;">AI-Powered Transformer Diagnostics</p>
        </div>

        ${includeSections.summary ? `
        <!-- Summary Section -->
        <div style="margin-bottom: 25px;">
          <h3 style="color: #1f2937; border-left: 4px solid #2563eb; padding-left: 10px; margin-bottom: 15px;">Analysis Summary</h3>
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td style="padding: 8px; border: 1px solid #e5e7eb; font-weight: bold; background-color: #f9fafb;">Asset ID</td>
              <td style="padding: 8px; border: 1px solid #e5e7eb;">${assetId}</td>
            </tr>
            <tr>
              <td style="padding: 8px; border: 1px solid #e5e7eb; font-weight: bold; background-color: #f9fafb;">Analysis Date</td>
              <td style="padding: 8px; border: 1px solid #e5e7eb;">${new Date(analysisData?.analysis_timestamp).toLocaleString()}</td>
            </tr>
            <tr>
              <td style="padding: 8px; border: 1px solid #e5e7eb; font-weight: bold; background-color: #f9fafb;">Fault Type</td>
              <td style="padding: 8px; border: 1px solid #e5e7eb;">${analysisData?.predicted_fault_type?.replace('_', ' ') || 'Unknown'}</td>
            </tr>
            <tr>
              <td style="padding: 8px; border: 1px solid #e5e7eb; font-weight: bold; background-color: #f9fafb;">Severity</td>
              <td style="padding: 8px; border: 1px solid #e5e7eb;">${analysisData?.severity_level || 'Unknown'}</td>
            </tr>
            <tr>
              <td style="padding: 8px; border: 1px solid #e5e7eb; font-weight: bold; background-color: #f9fafb;">Confidence</td>
              <td style="padding: 8px; border: 1px solid #e5e7eb;">${analysisData?.confidence_score ? (analysisData.confidence_score * 100).toFixed(1) + '%' : 'Unknown'}</td>
            </tr>
          </table>
        </div>
        ` : ''}

        ${includeSections.faultAnalysis && analysisData?.fault_probabilities ? `
        <!-- Fault Analysis Section -->
        <div style="margin-bottom: 25px;">
          <h3 style="color: #1f2937; border-left: 4px solid #2563eb; padding-left: 10px; margin-bottom: 15px;">Fault Probabilities</h3>
          <table style="width: 100%; border-collapse: collapse;">
            <tr style="background-color: #f9fafb;">
              <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left;">Fault Type</th>
              <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: right;">Probability</th>
            </tr>
            ${Object.entries(analysisData.fault_probabilities)
              .sort(([,a], [,b]) => b - a)
              .slice(0, 5)
              .map(([fault, probability]) => `
                <tr>
                  <td style="padding: 8px; border: 1px solid #e5e7eb;">${fault.replace('_', ' ')}</td>
                  <td style="padding: 8px; border: 1px solid #e5e7eb; text-align: right;">${(probability * 100).toFixed(2)}%</td>
                </tr>
              `).join('')}
          </table>
        </div>
        ` : ''}

        ${includeSections.recommendations && analysisData?.recommended_actions ? `
        <!-- Recommendations Section -->
        <div style="margin-bottom: 25px;">
          <h3 style="color: #1f2937; border-left: 4px solid #2563eb; padding-left: 10px; margin-bottom: 15px;">Maintenance Recommendations</h3>
          <ul style="margin: 0; padding-left: 20px;">
            ${analysisData.recommended_actions.map(action => `
              <li style="margin-bottom: 8px; color: #374151;">${action}</li>
            `).join('')}
          </ul>
        </div>
        ` : ''}

        <!-- Footer -->
        <div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center; color: #6b7280; font-size: 11px;">
          <p>Generated by UniFRA - Unified AI FRA Diagnostics Platform</p>
          <p>Report generated on ${new Date().toLocaleString()}</p>
        </div>
      </div>
    `;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] overflow-y-auto" data-testid="export-modal">
      <div className="flex items-end sm:items-center justify-center min-h-screen px-2 sm:px-4 text-center">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-900 opacity-75" onClick={onClose}></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="sm:flex sm:items-start">
              <div className="w-full">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4" data-testid="export-modal-title">
                  Export Analysis Report
                </h3>
                
                {/* Export Format Selection */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Export Format</label>
                  <select 
                    value={exportFormat} 
                    onChange={(e) => setExportFormat(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    data-testid="export-format-select"
                  >
                    <option value="pdf">PDF Report</option>
                    <option value="csv">CSV Data</option>
                    <option value="json">JSON Export</option>
                    <option value="image">PNG Image</option>
                  </select>
                </div>

                {/* Section Selection */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Include Sections</label>
                  <div className="space-y-2">
                    {Object.entries({
                      summary: 'Analysis Summary',
                      fraPlots: 'FRA Plots',
                      faultAnalysis: 'Fault Analysis',
                      explainability: 'ML Explainability',
                      recommendations: 'Recommendations',
                      rawData: 'Raw Data'
                    }).map(([key, label]) => (
                      <label key={key} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={includeSections[key]}
                          onChange={(e) => setIncludeSections(prev => ({
                            ...prev,
                            [key]: e.target.checked
                          }))}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          data-testid={`include-${key}`}
                        />
                        <span className="ml-2 text-sm text-gray-700">{label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Preview Toggle */}
                <div className="mb-4">
                  <button
                    onClick={() => setPreviewMode(!previewMode)}
                    className="text-sm text-blue-600 hover:text-blue-800"
                    data-testid="toggle-preview"
                  >
                    {previewMode ? 'Hide Preview' : 'Show Preview'}
                  </button>
                </div>

                {/* Preview Content */}
                {previewMode && (
                  <div 
                    ref={reportRef}
                    className="mb-4 p-4 border border-gray-200 rounded-lg bg-gray-50 max-h-64 overflow-y-auto text-xs"
                    data-testid="export-preview"
                    dangerouslySetInnerHTML={{ __html: generatePDFContent() }}
                  />
                )}
              </div>
            </div>
          </div>
          
          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={handleExport}
              disabled={isExporting}
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="export-button"
            >
              {isExporting ? 'Exporting...' : `Export ${exportFormat.toUpperCase()}`}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              data-testid="cancel-export"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportModal;