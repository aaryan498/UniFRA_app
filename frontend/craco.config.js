const path = require('path');

module.exports = {
  webpack: {
    configure: (webpackConfig, { env }) => {
      // Production optimizations
      if (env === 'production') {
        // Enable code splitting
        webpackConfig.optimization = {
          ...webpackConfig.optimization,
          splitChunks: {
            chunks: 'all',
            cacheGroups: {
              // Vendor chunk for node_modules
              vendor: {
                test: /[\\/]node_modules[\\/]/,
                name: 'vendors',
                priority: 10,
                reuseExistingChunk: true,
              },
              // Separate chunk for plotly (heavy library)
              plotly: {
                test: /[\\/]node_modules[\\/](plotly\.js|react-plotly\.js)[\\/]/,
                name: 'plotly',
                priority: 20,
                reuseExistingChunk: true,
              },
              // Common chunk for shared code
              common: {
                minChunks: 2,
                priority: 5,
                reuseExistingChunk: true,
              },
            },
          },
          runtimeChunk: 'single',
          minimize: true,
        };

        // Disable source maps in production
        webpackConfig.devtool = false;
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
