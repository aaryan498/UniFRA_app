const path = require('path');
const CompressionWebpackPlugin = require('compression-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');

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
          maxSize: 244000, // 244KB max chunk size for optimal loading
          cacheGroups: {
            // Separate chunk for plotly (3MB library) - highest priority
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
              enforce: true,
            },
            // Separate chunk for PDF/export libraries
            exportLibs: {
              test: /[\\/]node_modules[\\/](jspdf|html2canvas)[\\/]/,
              name: 'export-libs',
              priority: 30,
              reuseExistingChunk: true,
              enforce: true,
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
        usedExports: true, // Enable tree shaking
        sideEffects: false, // Aggressive tree shaking
      };

      // Production-specific optimizations
      if (env === 'production') {
        // Disable source maps to reduce bundle size
        webpackConfig.devtool = false;
        
        // Enhanced minification with Terser
        webpackConfig.optimization.minimizer = [
          new TerserPlugin({
            terserOptions: {
              parse: {
                ecma: 8,
              },
              compress: {
                ecma: 5,
                warnings: false,
                comparisons: false,
                inline: 2,
                drop_console: true, // Remove console.logs in production
                drop_debugger: true,
                pure_funcs: ['console.log', 'console.info', 'console.debug'],
              },
              mangle: {
                safari10: true,
              },
              output: {
                ecma: 5,
                comments: false,
                ascii_only: true,
              },
            },
            parallel: true,
            extractComments: false,
          }),
        ];

        // Add compression plugins for production
        webpackConfig.plugins.push(
          new CompressionWebpackPlugin({
            filename: '[path][base].gz',
            algorithm: 'gzip',
            test: /\.(js|css|html|svg)$/,
            threshold: 10240, // Only compress files > 10KB
            minRatio: 0.8,
          })
        );

        // Additional performance optimizations
        webpackConfig.performance = {
          maxEntrypointSize: 512000, // 500KB
          maxAssetSize: 512000,
          hints: 'warning',
        };
      }

      // Development optimizations for memory efficiency
      if (env === 'development') {
        // Faster rebuild times and lower memory usage
        webpackConfig.cache = {
          type: 'filesystem',
          buildDependencies: {
            config: [__filename],
          },
        };
        webpackConfig.optimization.removeAvailableModules = false;
        webpackConfig.optimization.removeEmptyChunks = false;
        // Simplify code splitting in development
        webpackConfig.optimization.splitChunks = {
          chunks: 'async',
          cacheGroups: {
            defaultVendors: {
              test: /[\\/]node_modules[\\/]/,
              priority: -10,
              reuseExistingChunk: true,
            },
            default: {
              minChunks: 2,
              priority: -20,
              reuseExistingChunk: true,
            },
          },
        };
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
  devServer: {
    compress: true,
    hot: true,
    client: {
      overlay: {
        errors: true,
        warnings: false,
      },
    },
  },
};