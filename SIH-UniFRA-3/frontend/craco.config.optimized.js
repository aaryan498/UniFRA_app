const webpack = require('webpack');
const CompressionPlugin = require('compression-webpack-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

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
              // Separate chunk for recharts
              recharts: {
                test: /[\\/]node_modules[\\/](recharts)[\\/]/,
                name: 'recharts',
                priority: 20,
                reuseExistingChunk: true,
              },
              // Separate chunk for radix-ui components
              radixui: {
                test: /[\\/]node_modules[\\/](@radix-ui)[\\/]/,
                name: 'radixui',
                priority: 15,
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

        // Add compression plugin
        webpackConfig.plugins.push(
          new CompressionPlugin({
            filename: '[path][base].gz',
            algorithm: 'gzip',
            test: /\.(js|css|html|svg)$/,
            threshold: 10240, // Only compress files > 10KB
            minRatio: 0.8,
          })
        );

        // Add bundle analyzer (only when ANALYZE=true)
        if (process.env.ANALYZE === 'true') {
          webpackConfig.plugins.push(
            new BundleAnalyzerPlugin({
              analyzerMode: 'static',
              reportFilename: 'bundle-report.html',
              openAnalyzer: false,
            })
          );
        }
      }

      // Resolve fallbacks for Node.js modules
      webpackConfig.resolve.fallback = {
        ...webpackConfig.resolve.fallback,
        crypto: false,
        stream: false,
        buffer: false,
        util: false,
      };

      // Ignore source maps in production
      if (env === 'production') {
        webpackConfig.devtool = false;
      }

      return webpackConfig;
    },
  },
  // Disable eslint overlay in development for better performance
  devServer: {
    client: {
      overlay: {
        errors: true,
        warnings: false,
      },
    },
  },
  // Babel configuration for optimal transpilation
  babel: {
    presets: [
      ['@babel/preset-react', { runtime: 'automatic' }],
    ],
    plugins: [
      // Add support for dynamic imports
      '@babel/plugin-syntax-dynamic-import',
    ],
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
