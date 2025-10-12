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
  const [exportSuccess, setExportSuccess] = useState(false);
  const reportRef = useRef();

  const handleExport = async () => {
    setIsExporting(true);
    setExportSuccess(false);
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
      setExportSuccess(true);
      setTimeout(() => {
        setExportSuccess(false);
        onClose();
      }, 2000);
    } catch (error) {
      console.error('Export failed:', error);
      alert(`Export failed: ${error.message}. Please try again.`);
    } finally {
      setIsExporting(false);
    }
  };

  const exportToPDF = async () => {
    // Create a temporary container for PDF generation
    const pdfContainer = document.createElement('div');
    pdfContainer.style.position = 'absolute';
    pdfContainer.style.left = '-9999px';
    pdfContainer.style.width = '794px'; // A4 width in pixels at 96 DPI
    pdfContainer.style.backgroundColor = '#ffffff';
    pdfContainer.innerHTML = generatePDFContent();
    document.body.appendChild(pdfContainer);

    try {
      // Capture the entire content with auto height
      const canvas = await html2canvas(pdfContainer, {
        scale: 2,
        useCORS: true,
        logging: false,
        width: 794,
        windowWidth: 794,
        backgroundColor: '#ffffff'
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      
      // Calculate how many pages we need
      const imgWidth = canvas.width;
      const imgHeight = canvas.height;
      const ratio = imgWidth / pdfWidth;
      const imgHeightInPDF = imgHeight / ratio;
      
      let heightLeft = imgHeightInPDF;
      let position = 0;
      
      // Add first page
      pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, imgHeightInPDF);
      heightLeft -= pdfHeight;
      
      // Add additional pages if needed
      while (heightLeft > 0) {
        position = heightLeft - imgHeightInPDF;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, imgHeightInPDF);
        heightLeft -= pdfHeight;
      }
      
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

    if (includeSections.summary && analysisData) {
      csvData.push(['Analysis Summary']);
      csvData.push(['Fault Type', analysisData.predicted_fault_type || 'Unknown']);
      csvData.push(['Severity', analysisData.severity_level || 'Unknown']);
      csvData.push(['Confidence', analysisData.confidence_score ? (analysisData.confidence_score * 100).toFixed(2) + '%' : 'N/A']);
      csvData.push(['Is Anomaly', analysisData.is_anomaly ? 'Yes' : 'No']);
      csvData.push(['Anomaly Score', analysisData.anomaly_score?.toFixed(3) || 'N/A']);
      csvData.push(['']);
    }

    if (includeSections.faultAnalysis && analysisData?.fault_probabilities) {
      csvData.push(['Fault Analysis']);
      csvData.push(['Fault Type', 'Probability']);
      Object.entries(analysisData.fault_probabilities).forEach(([fault, probability]) => {
        csvData.push([
          fault.replace(/_/g, ' '),
          (probability * 100).toFixed(2) + '%'
        ]);
      });
      csvData.push(['']);
    }

    if (includeSections.recommendations && analysisData?.recommended_actions) {
      csvData.push(['Maintenance Recommendations']);
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
      URL.revokeObjectURL(url);
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
          is_anomaly: analysisData?.is_anomaly,
          anomaly_score: analysisData?.anomaly_score
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
      URL.revokeObjectURL(url);
    }
  };

  const exportToImage = async () => {
    if (!reportRef.current) {
      // Create temporary preview if not shown
      const tempContainer = document.createElement('div');
      tempContainer.style.position = 'absolute';
      tempContainer.style.left = '-9999px';
      tempContainer.style.width = '1200px';
      tempContainer.style.backgroundColor = '#ffffff';
      tempContainer.style.padding = '40px';
      tempContainer.innerHTML = generatePDFContent();
      document.body.appendChild(tempContainer);

      try {
        const canvas = await html2canvas(tempContainer, {
          scale: 2,
          useCORS: true,
          logging: false,
          backgroundColor: '#ffffff'
        });

        const link = document.createElement('a');
        link.download = `FRA_Analysis_${assetId}_${new Date().toISOString().split('T')[0]}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
      } finally {
        document.body.removeChild(tempContainer);
      }
    } else {
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
    }
  };

  const generatePDFContent = () => {
    return `
      <div style="padding: 30px; font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; max-width: 750px;">
        <!-- Header -->
        <div style="text-align: center; border-bottom: 3px solid #2563eb; padding-bottom: 20px; margin-bottom: 30px;">
          <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 12px;">
            <svg width="45" height="45" fill="#2563eb" viewBox="0 0 24 24" style="margin-right: 12px;">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
            <h1 style="color: #2563eb; margin: 0; font-size: 28px; font-weight: 700;">UniFRA</h1>
          </div>
          <h2 style="color: #1f2937; margin: 0; font-size: 20px; font-weight: 600;">FRA Analysis Report</h2>
          <p style="color: #6b7280; margin: 8px 0 0 0; font-size: 13px;">AI-Powered Transformer Diagnostics</p>
        </div>

        ${includeSections.summary ? `
        <!-- Summary Section -->
        <div style="margin-bottom: 30px; background: #f9fafb; padding: 20px; border-radius: 8px;">
          <h3 style="color: #1f2937; border-left: 5px solid #2563eb; padding-left: 12px; margin: 0 0 20px 0; font-size: 18px; font-weight: 600;">Analysis Summary</h3>
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td style="padding: 12px; border: 1px solid #e5e7eb; font-weight: 600; background-color: #f3f4f6; width: 40%;">Asset ID</td>
              <td style="padding: 12px; border: 1px solid #e5e7eb;">${assetId}</td>
            </tr>
            <tr>
              <td style="padding: 12px; border: 1px solid #e5e7eb; font-weight: 600; background-color: #f3f4f6;">Analysis Date</td>
              <td style="padding: 12px; border: 1px solid #e5e7eb;">${new Date(analysisData?.analysis_timestamp).toLocaleString()}</td>
            </tr>
            <tr>
              <td style="padding: 12px; border: 1px solid #e5e7eb; font-weight: 600; background-color: #f3f4f6;">Fault Type</td>
              <td style="padding: 12px; border: 1px solid #e5e7eb;">${analysisData?.predicted_fault_type?.replace(/_/g, ' ').toUpperCase() || 'Unknown'}</td>
            </tr>
            <tr>
              <td style="padding: 12px; border: 1px solid #e5e7eb; font-weight: 600; background-color: #f3f4f6;">Severity</td>
              <td style="padding: 12px; border: 1px solid #e5e7eb;"><strong>${analysisData?.severity_level?.toUpperCase() || 'Unknown'}</strong></td>
            </tr>
            <tr>
              <td style="padding: 12px; border: 1px solid #e5e7eb; font-weight: 600; background-color: #f3f4f6;">Confidence</td>
              <td style="padding: 12px; border: 1px solid #e5e7eb; color: #059669; font-weight: 600;">${analysisData?.confidence_score ? (analysisData.confidence_score * 100).toFixed(1) + '%' : 'Unknown'}</td>
            </tr>
            <tr>
              <td style="padding: 12px; border: 1px solid #e5e7eb; font-weight: 600; background-color: #f3f4f6;">Anomaly Status</td>
              <td style="padding: 12px; border: 1px solid #e5e7eb; font-weight: 600; color: ${analysisData?.is_anomaly ? '#dc2626' : '#059669'};">${analysisData?.is_anomaly ? 'ANOMALY DETECTED' : 'NORMAL'}</td>
            </tr>
          </table>
        </div>
        ` : ''}

        ${includeSections.faultAnalysis && analysisData?.fault_probabilities ? `
        <!-- Fault Analysis Section -->
        <div style="margin-bottom: 30px;">
          <h3 style="color: #1f2937; border-left: 5px solid #2563eb; padding-left: 12px; margin: 0 0 20px 0; font-size: 18px; font-weight: 600;">Fault Probabilities</h3>
          <table style="width: 100%; border-collapse: collapse;">
            <tr style="background-color: #f3f4f6;">
              <th style="padding: 12px; border: 1px solid #e5e7eb; text-align: left; font-weight: 600;">Fault Type</th>
              <th style="padding: 12px; border: 1px solid #e5e7eb; text-align: right; font-weight: 600;">Probability</th>
            </tr>
            ${Object.entries(analysisData.fault_probabilities)
              .sort(([,a], [,b]) => b - a)
              .slice(0, 8)
              .map(([fault, probability]) => `
                <tr>
                  <td style="padding: 10px; border: 1px solid #e5e7eb;">${fault.replace(/_/g, ' ').toUpperCase()}</td>
                  <td style="padding: 10px; border: 1px solid #e5e7eb; text-align: right; font-weight: 600;">${(probability * 100).toFixed(2)}%</td>
                </tr>
              `).join('')}
          </table>
        </div>
        ` : ''}

        ${includeSections.recommendations && analysisData?.recommended_actions ? `
        <!-- Recommendations Section -->
        <div style="margin-bottom: 30px; background: #fef3c7; padding: 20px; border-radius: 8px; border-left: 5px solid #f59e0b;">
          <h3 style="color: #92400e; margin: 0 0 15px 0; font-size: 18px; font-weight: 600;">⚠️ Maintenance Recommendations</h3>
          <ul style="margin: 0; padding-left: 20px; color: #78350f;">
            ${analysisData.recommended_actions.map(action => `
              <li style="margin-bottom: 10px; font-size: 14px;"><strong>${action}</strong></li>
            `).join('')}
          </ul>
        </div>
        ` : ''}

        <!-- Footer -->
        <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e5e7eb; text-align: center; color: #6b7280; font-size: 12px;">
          <p style="margin: 5px 0;"><strong>Generated by UniFRA</strong> - Unified AI FRA Diagnostics Platform</p>
          <p style="margin: 5px 0;">Report generated on ${new Date().toLocaleString()}</p>
          <p style="margin: 5px 0; font-style: italic;">This is an automated analysis report. Please verify critical findings with domain experts.</p>
        </div>
      </div>
    `;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[70] overflow-y-auto" data-testid="export-modal">
      <div className="flex items-end sm:items-center justify-center min-h-screen px-2 sm:px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Backdrop with improved animation */}
        <div 
          className="fixed inset-0 transition-opacity duration-300 ease-out" 
          aria-hidden="true"
          onClick={onClose}
        >
          <div className="absolute inset-0 bg-gray-900 opacity-75"></div>
        </div>

        {/* Center modal vertically trick */}
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        {/* Modal Content - Fully Responsive */}
        <div className="inline-block align-bottom bg-white rounded-t-2xl sm:rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl w-full">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-4 sm:px-6 py-4 sm:py-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="bg-white bg-opacity-20 p-2 rounded-lg">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg sm:text-xl font-bold text-white" data-testid="export-modal-title">
                    Export Analysis Report
                  </h3>
                  <p className="text-xs sm:text-sm text-blue-100 mt-0.5">Choose format and sections to export</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-white hover:bg-opacity-20 transition-all duration-200 active:scale-95"
                aria-label="Close"
              >
                <svg className="w-5 h-5 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="bg-white px-4 sm:px-6 py-5 sm:py-6">
            <div className="space-y-5">
              {/* Export Format Selection */}
              <div>
                <label className="block text-sm font-semibold text-gray-800 mb-2.5">
                  📄 Export Format
                </label>
                <select 
                  value={exportFormat} 
                  onChange={(e) => setExportFormat(e.target.value)}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-sm font-medium bg-white hover:border-blue-400"
                  data-testid="export-format-select"
                >
                  <option value="pdf">📕 PDF Report (Recommended)</option>
                  <option value="csv">📊 CSV Data Export</option>
                  <option value="json">🔧 JSON Technical Export</option>
                  <option value="image">🖼️ PNG Image Export</option>
                </select>
                <p className="mt-2 text-xs text-gray-500">
                  {exportFormat === 'pdf' && '✓ Best for sharing complete reports with formatted content'}
                  {exportFormat === 'csv' && '✓ Best for data analysis in spreadsheet applications'}
                  {exportFormat === 'json' && '✓ Best for programmatic access and integration'}
                  {exportFormat === 'image' && '✓ Best for quick sharing and presentations'}
                </p>
              </div>

              {/* Section Selection */}
              <div>
                <label className="block text-sm font-semibold text-gray-800 mb-2.5">
                  📋 Include Sections
                </label>
                <div className="space-y-2.5 bg-gray-50 p-4 rounded-lg border border-gray-200">
                  {Object.entries({
                    summary: 'Analysis Summary',
                    fraPlots: 'FRA Plots',
                    faultAnalysis: 'Fault Analysis',
                    explainability: 'ML Explainability',
                    recommendations: 'Recommendations',
                    rawData: 'Raw Data (Large Size)'
                  }).map(([key, label]) => (
                    <label key={key} className="flex items-center p-2.5 hover:bg-white rounded-lg transition-colors duration-200 cursor-pointer group">
                      <input
                        type="checkbox"
                        checked={includeSections[key]}
                        onChange={(e) => setIncludeSections(prev => ({
                          ...prev,
                          [key]: e.target.checked
                        }))}
                        className="w-4 h-4 rounded border-2 border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500 transition-all cursor-pointer"
                        data-testid={`include-${key}`}
                      />
                      <span className="ml-3 text-sm font-medium text-gray-700 group-hover:text-gray-900">{label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Preview Toggle */}
              <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  <span className="text-sm font-semibold text-blue-900">Preview Report</span>
                </div>
                <button
                  onClick={() => setPreviewMode(!previewMode)}
                  className="px-4 py-2 text-sm font-medium text-blue-700 hover:text-blue-800 hover:bg-blue-100 rounded-lg transition-all duration-200 active:scale-95"
                  data-testid="toggle-preview"
                >
                  {previewMode ? 'Hide Preview' : 'Show Preview'}
                </button>
              </div>

              {/* Preview Content */}
              {previewMode && (
                <div 
                  ref={reportRef}
                  className="border-2 border-gray-300 rounded-lg bg-white max-h-96 overflow-y-auto text-xs shadow-inner"
                  data-testid="export-preview"
                  style={{ scrollBehavior: 'smooth' }}
                  dangerouslySetInnerHTML={{ __html: generatePDFContent() }}
                />
              )}

              {/* Success Message */}
              {exportSuccess && (
                <div className="p-4 bg-green-50 border-2 border-green-200 rounded-lg flex items-center gap-3 animate-fadeIn">
                  <svg className="w-6 h-6 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <p className="text-sm font-semibold text-green-900">Export Successful!</p>
                    <p className="text-xs text-green-700">Your file has been downloaded</p>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Footer */}
          <div className="bg-gray-50 px-4 sm:px-6 py-4 sm:flex sm:flex-row-reverse gap-3 border-t border-gray-200">
            <button
              type="button"
              onClick={handleExport}
              disabled={isExporting || exportSuccess}
              className="w-full sm:w-auto inline-flex justify-center items-center gap-2 rounded-lg border border-transparent shadow-sm px-5 py-2.5 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 active:scale-95"
              data-testid="export-button"
            >
              {isExporting ? (
                <>
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Exporting...</span>
                </>
              ) : exportSuccess ? (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Exported!</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  <span>Export {exportFormat.toUpperCase()}</span>
                </>
              )}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={isExporting}
              className="mt-3 sm:mt-0 w-full sm:w-auto inline-flex justify-center rounded-lg border-2 border-gray-300 shadow-sm px-5 py-2.5 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 active:scale-95"
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
