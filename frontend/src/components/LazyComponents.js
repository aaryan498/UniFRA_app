import React, { lazy, Suspense } from 'react';

// Loading fallback component
const LoadingFallback = ({ message = 'Loading...' }) => (
  <div className="flex items-center justify-center p-8">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p className="text-gray-600">{message}</p>
    </div>
  </div>
);

// Lazy load heavy components
export const SystemStatus = lazy(() => import('./SystemStatus'));
export const AnalysisDetailView = lazy(() => import('./AnalysisDetailView'));
export const AssetHistory = lazy(() => import('./AssetHistory'));
export const UploadAnalysis = lazy(() => import('./UploadAnalysis'));

// Lazy load visualization components
export const FRAFrequencyPlot = lazy(() => import('./visualizations/FRAFrequencyPlot'));
export const FaultProbabilityChart = lazy(() => import('./visualizations/FaultProbabilityChart'));
export const ExplainabilityPlot = lazy(() => import('./visualizations/ExplainabilityPlot'));
export const AnomalyHeatmap = lazy(() => import('./visualizations/AnomalyHeatmap'));

// Wrapper component with Suspense
export const LazySystemStatus = (props) => (
  <Suspense fallback={<LoadingFallback message="Loading System Status..." />}>
    <SystemStatus {...props} />
  </Suspense>
);

export const LazyAnalysisDetailView = (props) => (
  <Suspense fallback={<LoadingFallback message="Loading Analysis Details..." />}>
    <AnalysisDetailView {...props} />
  </Suspense>
);

export const LazyAssetHistory = (props) => (
  <Suspense fallback={<LoadingFallback message="Loading Asset History..." />}>
    <AssetHistory {...props} />
  </Suspense>
);

export const LazyUploadAnalysis = (props) => (
  <Suspense fallback={<LoadingFallback message="Loading Upload Interface..." />}>
    <UploadAnalysis {...props} />
  </Suspense>
);

export const LazyFRAFrequencyPlot = (props) => (
  <Suspense fallback={<LoadingFallback message="Loading Chart..." />}>
    <FRAFrequencyPlot {...props} />
  </Suspense>
);

export const LazyFaultProbabilityChart = (props) => (
  <Suspense fallback={<LoadingFallback message="Loading Chart..." />}>
    <FaultProbabilityChart {...props} />
  </Suspense>
);

export const LazyExplainabilityPlot = (props) => (
  <Suspense fallback={<LoadingFallback message="Loading Explainability Plot..." />}>
    <ExplainabilityPlot {...props} />
  </Suspense>
);

export const LazyAnomalyHeatmap = (props) => (
  <Suspense fallback={<LoadingFallback message="Loading Heatmap..." />}>
    <AnomalyHeatmap {...props} />
  </Suspense>
);

export default {
  SystemStatus: LazySystemStatus,
  AnalysisDetailView: LazyAnalysisDetailView,
  AssetHistory: LazyAssetHistory,
  UploadAnalysis: LazyUploadAnalysis,
  FRAFrequencyPlot: LazyFRAFrequencyPlot,
  FaultProbabilityChart: LazyFaultProbabilityChart,
  ExplainabilityPlot: LazyExplainabilityPlot,
  AnomalyHeatmap: LazyAnomalyHeatmap,
};
