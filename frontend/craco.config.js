const path = require('path');

module.exports = {
  webpack: {
    configure: (webpackConfig, { env }) => {
      // Configure path alias for @ imports
      webpackConfig.resolve.alias = {
        ...webpackConfig.resolve.alias,
        '@': path.resolve(__dirname, 'src'),
      };

      // Aggressive code splitting for both dev and production
      webpackConfig.optimization = {
        ...webpackConfig.optimization,
        splitChunks: {
          chunks: 'all',
          maxInitialRequests: 30,
          minSize: 20000,
          maxSize: 244000, // 244KB max chunk size
          cacheGroups: {
            // Separate chunk for plotly (3MB library)
            plotly: {
              test: /[\\/]node_modules[\\/](plotly\.js|react-plotly\.js)[\\/]/,
              name: 'plotly',
              priority: 40,
              reuseExistingChunk: true,
              enforce: true,
            },
            // Separate chunk for recharts
            recharts: {
              test: /[\\/]node_modules[\\/]recharts[\\/]/,
              name: 'recharts',
              priority: 35,
              reuseExistingChunk: true,
            },
            // Separate chunk for PDF/export libraries
            exportLibs: {
              test: /[\\/]node_modules[\\/](jspdf|html2canvas)[\\/]/,
              name: 'export-libs',
              priority: 30,
              reuseExistingChunk: true,
            },
            // Radix UI components
            radixUI: {
              test: /[\\/]node_modules[\\/]@radix-ui[\\/]/,
              name: 'radix-ui',
              priority: 25,
              reuseExistingChunk: true,
            },
            // React and core libraries
            reactVendor: {
              test: /[\\/]node_modules[\\/](react|react-dom|react-router-dom)[\\/]/,
              name: 'react-vendor',
              priority: 20,
              reuseExistingChunk: true,
            },
            // Other vendor libraries
            vendors: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendors',
              priority: 10,
              reuseExistingChunk: true,
            },
            // Common code used across app
            common: {
              minChunks: 2,
              priority: 5,
              reuseExistingChunk: true,
            },
          },
        },
        runtimeChunk: 'single',
      };

      // Production-specific optimizations
      if (env === 'production') {
        // Disable source maps to reduce bundle size
        webpackConfig.devtool = false;
        
        // Enable minimize
        webpackConfig.optimization.minimize = true;
      }

      return webpackConfig;
    },
  },
  style: {
    postcss: {
      mode: 'extends',
      loaderOptions: {
        postcssOptions: {
          ident: 'postcss',
          plugins: [
            require('tailwindcss'),
            require('autoprefixer'),
          ],
        },
      },
    },
  },
};
