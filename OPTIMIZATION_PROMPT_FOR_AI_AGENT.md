# 🚀 FRONTEND OPTIMIZATION - IMPLEMENTATION PROMPT
## Copy this entire prompt and paste it to Emergent AI Agent

---

**OBJECTIVE**: Optimize the UniFRA frontend to load in under 3 seconds on development server without removing ANY existing functionality. Focus on replacing heavy dependencies with lightweight alternatives and implementing proper lazy loading.

**CRITICAL RULES**:
1. ❌ DO NOT remove any features or UI components
2. ❌ DO NOT alter the look and feel of the application  
3. ❌ DO NOT change any API endpoints or backend integration
4. ✅ DO replace heavy libraries with lightweight equivalents
5. ✅ DO implement proper lazy loading and code splitting
6. ✅ DO test each change to ensure functionality is preserved

---

## 📋 IMPLEMENTATION CHECKLIST

### **PHASE 1: CRITICAL DEPENDENCY REPLACEMENTS**

#### **TASK 1.1: Replace Plotly.js with Plotly Basic (HIGHEST PRIORITY)**
**What**: Replace 312MB `plotly.js` with 2.5MB `plotly.js-basic-dist-min`
**Why**: 98% size reduction, only includes chart types we actually use
**Impact**: -5 seconds load time

**Steps**:
```bash
# 1. Remove current plotly
cd /app/frontend
yarn remove plotly.js

# 2. Install minimal bundle  
yarn add plotly.js-basic-dist-min@2.35.0
```

**Code Changes**:
```javascript
// Update ALL visualization files:
// - /src/components/visualizations/FRAFrequencyPlot.js
// - /src/components/visualizations/FaultProbabilityChart.js  
// - /src/components/visualizations/ExplainabilityPlot.js
// - /src/components/visualizations/AnomalyHeatmap.js
// - /src/components/SystemStatus.js

// In each file, REPLACE:
import Plot from 'react-plotly.js';

// WITH:
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-basic-dist-min';
const Plot = createPlotlyComponent(Plotly);
```

**Testing**:
- Navigate to "Upload & Analyze" and verify FRA charts render correctly
- Navigate to "System Status" and verify all plots display
- Check that all interactive features (zoom, pan, hover) still work
- Ensure export to PNG functionality still works

---

#### **TASK 1.2: Implement Dynamic Import for Export Libraries**
**What**: Load jsPDF and html2canvas only when user clicks export
**Why**: 33.6MB of dependencies user rarely uses
**Impact**: -1.5 seconds load time

**Code Changes**:
```javascript
// File: /src/components/export/ExportModal.js

// REMOVE these imports from top of file:
// import { jsPDF } from 'jspdf';
// import html2canvas from 'html2canvas';

// UPDATE the handleExport function:
const handleExport = async () => {
  setIsExporting(true);
  try {
    // Load libraries dynamically when needed
    const { jsPDF } = await import(/* webpackChunkName: "jspdf" */ 'jspdf');
    const html2canvas = (await import(/* webpackChunkName: "html2canvas" */ 'html2canvas')).default;
    
    switch (exportFormat) {
      case 'pdf':
        await exportToPDF(jsPDF, html2canvas);
        break;
      case 'image':
        await exportToImage(html2canvas);
        break;
      // ... rest of cases
    }
  } catch (error) {
    console.error('Export failed:', error);
    alert('Export failed. Please try again.');
  } finally {
    setIsExporting(false);
  }
};

// UPDATE function signatures to accept the imported libraries:
const exportToPDF = async (jsPDF, html2canvas) => {
  const doc = new jsPDF();
  // ... rest of PDF export logic
};

const exportToImage = async (html2canvas) => {
  // ... rest of image export logic
};
```

**Testing**:
- Navigate to analysis results page
- Click "Export" button
- Verify PDF export still works correctly
- Verify image export still works correctly
- Check that CSV and JSON exports work (these don't need the libraries)

---

#### **TASK 1.3: Downgrade React to Stable Version 18.3**
**What**: Replace React 19.0.0 with React 18.3.1
**Why**: React 19 is too new, causes dev server instability
**Impact**: +95% stability, faster hot reload

**Steps**:
```bash
cd /app/frontend

# Remove React 19
yarn remove react react-dom react-is

# Install stable React 18.3
yarn add react@18.3.1 react-dom@18.3.1 react-is@18.3.1

# Update package.json if needed
```

**Testing**:
- Restart development server: `yarn start`
- Verify login page loads correctly
- Navigate through all sections: Dashboard, Upload, History, System Status
- Verify no console errors related to React
- Test authentication flow (guest login, email login)
- Verify all interactive elements work (dropdowns, modals, forms)

---

### **PHASE 2: CODE SPLITTING & LAZY LOADING OPTIMIZATION**

#### **TASK 2.1: Optimize Recharts Imports (Tree Shaking)**
**What**: Import only needed Recharts components individually
**Why**: Reduce 7.3MB import to ~500KB
**Impact**: -1 second load time

**Code Changes**:
```javascript
// File: /src/components/UploadAnalysis.js
// File: /src/components/AssetHistory.js

// REPLACE the barrel import:
// import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// WITH individual imports:
import LineChart from 'recharts/lib/chart/LineChart';
import Line from 'recharts/lib/cartesian/Line';
import XAxis from 'recharts/lib/cartesian/XAxis';
import YAxis from 'recharts/lib/cartesian/YAxis';
import CartesianGrid from 'recharts/lib/cartesian/CartesianGrid';
import Tooltip from 'recharts/lib/component/Tooltip';
import Legend from 'recharts/lib/component/Legend';
import ResponsiveContainer from 'recharts/lib/component/ResponsiveContainer';
```

**Testing**:
- Navigate to "Upload & Analyze"
- Upload a test FRA file
- Verify the preview chart renders correctly
- Navigate to "Asset History"
- Verify history charts display properly

---

#### **TASK 2.2: Optimize Webpack Dev Configuration**
**What**: Simplify code splitting in development mode
**Why**: Faster rebuilds, lower memory usage
**Impact**: -2 seconds load time, -40% memory

**Code Changes**:
```javascript
// File: /app/frontend/craco.config.js

// REPLACE the development section (lines 136-162):
if (env === 'development') {
  // Filesystem cache for fast rebuilds
  webpackConfig.cache = {
    type: 'filesystem',
    buildDependencies: {
      config: [__filename],
    },
  };
  
  // Disable code splitting in dev for faster loads
  webpackConfig.optimization.splitChunks = false;
  webpackConfig.optimization.runtimeChunk = false;
  
  // Faster rebuild times
  webpackConfig.optimization.removeAvailableModules = false;
  webpackConfig.optimization.removeEmptyChunks = false;
  webpackConfig.optimization.usedExports = false;
  
  // Fastest source maps for development
  webpackConfig.devtool = 'eval-cheap-module-source-map';
  
  // Reduce memory usage
  webpackConfig.optimization.minimize = false;
}
```

**Testing**:
- Restart development server
- Measure initial load time (should be under 3 seconds)
- Make a code change and verify hot reload works
- Check memory usage with `ps aux | grep node`

---

#### **TASK 2.3: Implement Aggressive Lazy Loading**
**What**: Lazy load Header, Sidebar, and Dashboard components
**Why**: Reduce initial bundle size
**Impact**: -0.8 seconds load time

**Code Changes**:
```javascript
// File: /src/App.js

// ADD these lazy imports at the top (after existing lazy imports):
const Dashboard = lazy(() => import('./components/Dashboard'));
const Header = lazy(() => import('./components/Header'));
const Sidebar = lazy(() => import('./components/Sidebar'));

// WRAP the authenticated app section with Suspense:
if (!user) {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <Login onLogin={handleLogin} />
      </div>
    </GoogleOAuthProvider>
  );
}

return (
  <Router>
    <div className="App">
      <Suspense fallback={
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="text-gray-600 mt-4">Loading dashboard...</p>
        </div>
      }>
        <div className="app-layout">
          <Sidebar 
            isOpen={sidebarOpen}
            activeView={activeView}
            onViewChange={setActiveView}
            onToggle={() => setSidebarOpen(!sidebarOpen)}
            systemStatus={systemStatus}
          />

          <div className={`main-content ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
            <Header 
              user={user}
              onMenuClick={() => setSidebarOpen(!sidebarOpen)}
              onRefresh={refreshData}
              onLogout={handleLogout}
              systemStatus={systemStatus}
            />

            <div className="content-area">
              <Routes>
                <Route path="/" element={
                  <>
                    {activeView === 'dashboard' && (
                      <Dashboard 
                        user={user}
                        assets={assets}
                        systemStatus={systemStatus}
                        onRefresh={refreshData}
                      />
                    )}
                    {/* ... rest of routes */}
                  </>
                } />
              </Routes>
            </div>
          </div>
        </div>
      </Suspense>
    </div>
  </Router>
);
```

**Testing**:
- Login and verify dashboard loads
- Check that loading spinner appears briefly
- Verify all navigation works correctly

---

### **PHASE 3: OPTIONAL PERFORMANCE ENHANCEMENTS**

#### **TASK 3.1: Replace Axios with Lightweight Alternative (OPTIONAL)**
**What**: Replace axios (2.5MB) with ky (10KB)
**Why**: 99.6% size reduction
**Impact**: -0.5 seconds load time

**Only do this if you have time. It's not critical.**

**Steps**:
```bash
cd /app/frontend
yarn remove axios
yarn add ky@1.7.3
```

**Code Changes**:
```javascript
// Create new file: /src/utils/api.js
import ky from 'ky';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const api = ky.create({
  prefixUrl: `${BACKEND_URL}/api`,
  timeout: 30000,
  credentials: 'include',
  hooks: {
    beforeRequest: [
      request => {
        const token = localStorage.getItem('access_token');
        if (token) {
          request.headers.set('Authorization', `Bearer ${token}`);
        }
      }
    ],
    afterResponse: [
      async (request, options, response) => {
        if (!response.ok && response.status === 401) {
          // Handle authentication errors
          localStorage.removeItem('access_token');
          window.location.href = '/';
        }
      }
    ]
  }
});

export default api;

// Helper methods for common patterns
export const apiGet = (endpoint) => api.get(endpoint).json();
export const apiPost = (endpoint, data) => api.post(endpoint, { json: data }).json();
export const apiPut = (endpoint, data) => api.put(endpoint, { json: data }).json();
export const apiDelete = (endpoint) => api.delete(endpoint).json();
```

**Then update all files using axios**:
```javascript
// BEFORE:
import axios from 'axios';
const response = await axios.get(`${API}/health`);

// AFTER:
import api from '@/utils/api';
const data = await api.get('health').json();
```

---

## 🧪 COMPREHENSIVE TESTING PROTOCOL

After completing each phase, run these tests:

### **Functional Testing**:
1. ✅ Guest login works
2. ✅ Email registration/login works  
3. ✅ Dashboard displays correctly with user stats
4. ✅ File upload works
5. ✅ ML analysis completes successfully
6. ✅ FRA charts render correctly
7. ✅ Fault probability charts display
8. ✅ Asset history loads
9. ✅ System status page shows metrics
10. ✅ Export functionality works (PDF, CSV, JSON, Image)
11. ✅ Navigation between pages works
12. ✅ Logout works
13. ✅ Mobile responsive design intact
14. ✅ All interactive elements functional (dropdowns, modals, forms)

### **Performance Testing**:
```bash
# Measure load time
1. Clear browser cache
2. Open DevTools Network tab
3. Navigate to app URL
4. Record "Load" time - should be under 3 seconds

# Measure memory usage
ps aux | grep node

# Should show:
# - Development server: < 800MB (down from 2-3GB)
# - Production build time: < 45 seconds (down from 75s)
```

### **Development Experience Testing**:
1. Start dev server - should start in under 10 seconds
2. Make code change - hot reload should complete in under 2 seconds
3. Run for 30 minutes - should not crash or slow down
4. Build production - should complete in under 45 seconds

---

## ⚠️ IMPORTANT NOTES

### **If You Encounter Issues**:

**Issue**: Plotly charts break after switching to basic bundle
- **Solution**: Check if you're using 3D plots, maps, or statistical charts. These aren't in the basic bundle. Switch those specific charts to Recharts.

**Issue**: Export functionality breaks with dynamic imports
- **Solution**: Verify webpack chunk names are correct. Check browser DevTools for loading errors.

**Issue**: React 18 downgrade causes errors
- **Solution**: Check for React 19-specific features in code (like `use` hook, new Suspense behaviors). Remove or replace them.

**Issue**: Development server still slow after optimizations
- **Solution**: Clear webpack cache: `rm -rf node_modules/.cache` and restart.

**Issue**: Hot reload stops working
- **Solution**: Check craco.config.js for syntax errors. Revert to original config and apply changes one by one.

---

## 📊 SUCCESS CRITERIA

Before considering the optimization complete, verify:

- [  ] ✅ Development server loads in **under 3 seconds**
- [  ] ✅ Development server **never crashes** during normal use
- [  ] ✅ Hot reload completes in **under 2 seconds**
- [  ] ✅ Production build completes in **under 45 seconds**
- [  ] ✅ Production bundle size **under 3MB**
- [  ] ✅ All 14 functional tests pass
- [  ] ✅ No visual or UX changes
- [  ] ✅ No features removed or broken
- [  ] ✅ Memory usage **under 800MB** in development

---

## 🎯 EXECUTION ORDER

**DO THESE IN ORDER:**

1. **First**: Task 1.1 (Replace Plotly) - Biggest impact
2. **Second**: Task 1.2 (Dynamic import exports) - Quick win
3. **Third**: Task 1.3 (React 18 downgrade) - Stability fix
4. **Fourth**: Task 2.2 (Webpack config) - Development speed
5. **Fifth**: Task 2.1 (Recharts optimization) - Bundle size
6. **Sixth**: Task 2.3 (Aggressive lazy loading) - Initial load
7. **Optional**: Task 3.1 (Replace axios) - If time permits

**After each task:**
- Test the specific feature affected
- Measure load time
- Commit changes with clear message
- Move to next task

---

## 🚨 CRITICAL REMINDERS

1. **NEVER remove functionality** - only optimize how it's loaded
2. **ALWAYS test after each change** - don't break what works
3. **Keep the UI identical** - users should see no difference
4. **Measure everything** - use DevTools to verify improvements
5. **Document issues** - if something doesn't work, note why

---

## 📝 FINAL DELIVERABLES

When complete, provide:

1. ✅ Summary of changes made
2. ✅ Before/after load time comparison
3. ✅ Before/after bundle size comparison
4. ✅ List of all 14 functional tests passed
5. ✅ Any issues encountered and how they were resolved
6. ✅ Screenshots of DevTools showing load time under 3 seconds

---

**START IMPLEMENTATION NOW** - Follow the tasks in order and test thoroughly after each change. Good luck! 🚀
