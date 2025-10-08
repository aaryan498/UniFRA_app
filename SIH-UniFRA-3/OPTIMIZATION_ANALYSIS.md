# UniFRA Optimization Analysis

## Frontend Dependencies Audit

### Heavy Dependencies (Need Lazy Loading):
1. **plotly.js** (3.1.1) - ~3MB - Used in 5 components
2. **plotly.js-dist-min** (3.1.1) - DUPLICATE - Can be removed
3. **react-plotly.js** (2.6.0) - Wrapper for plotly
4. **d3** (7.9.0) - ~500KB - Types only, not actually used
5. **chart.js** (4.5.0) - ~200KB - Not used
6. **recharts** (3.2.1) - ~400KB - Used in 2 components
7. **jspdf** (3.0.3) - ~300KB - For PDF export (not yet implemented)
8. **html2canvas** (1.4.1) - ~200KB - For image export (not yet implemented)

### Radix UI Components - Many Unused:
- 24 @radix-ui packages installed
- Only ~5-6 actually used (dialog, dropdown-menu, avatar, tabs, toast)
- Rest can be removed: accordion, alert-dialog, aspect-ratio, checkbox, collapsible, context-menu, hover-card, label, menubar, navigation-menu, popover, progress, radio-group, scroll-area, select, separator, slider, switch, toggle, toggle-group, tooltip

### Other Unused Dependencies:
- **@types/d3** - TypeScript types but project uses JS
- **@types/js-cookie** - TypeScript types but project uses JS
- **cra-template** - Only needed during initial create-react-app
- **cmdk** - Command menu, not used
- **embla-carousel-react** - Carousel, not used
- **input-otp** - OTP input, not used (we built custom)
- **next-themes** - Theme switching, not used
- **react-day-picker** - Date picker, not used
- **react-hook-form** - Form validation, not used
- **@hookform/resolvers** - Form validation, not used
- **react-resizable-panels** - Resizable panels, not used
- **sonner** - Toast notifications, not used (using custom)
- **vaul** - Drawer component, not used
- **zod** - Schema validation, not used
- **class-variance-authority** - CSS utility, minimal use
- **lucide-react** - Icons, not used (using inline SVGs)
- **date-fns** - Date formatting, can use native methods

## Backend Dependencies Audit

### Potentially Unused:
- **torch** (2.8.0) - ~800MB - Only if ML models not using it
- **torchvision** (0.23.0) - ~300MB - Image processing, likely unused
- **lime** (0.2.0.1) - ML explainability, not yet implemented
- **shap** (0.48.0) - ML explainability, not yet implemented
- **xgboost** (3.0.5) - ML model, check if used
- **seaborn** (0.13.2) - Visualization, likely unused in backend
- **matplotlib** (3.10.6) - Visualization, likely unused in backend
- **stripe** (13.0.1) - Payment processing, not implemented

## Optimization Strategies

### 1. Code Splitting & Lazy Loading:
- Lazy load Plotly components (SystemStatus, visualizations)
- Lazy load heavy route components
- Dynamic imports for PDF/image export

### 2. Dependency Cleanup:
- Remove ~15 unused frontend packages
- Remove ~8 unused backend packages
- Use plotly.js-dist-min only (remove full plotly.js)

### 3. Build Optimization:
- Enable React production mode
- Configure webpack code splitting
- Add bundle analyzer
- Compress assets

### 4. Expected Improvements:
- Bundle size reduction: ~40-50%
- Initial load time: <3 seconds (from ~8-10 seconds)
- Memory usage during build: Reduced by ~30%
- Faster hot reload in development
