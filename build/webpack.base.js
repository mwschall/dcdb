const os = require('os')
const path = require('path')
const VueLoaderPlugin = require('vue-loader/lib/plugin')
const BundleTracker = require('webpack-bundle-tracker')

module.exports = {
  context: path.resolve(__dirname, '../'),
  entry: {
    app: './src',
  },
  output: {
    path: path.resolve(__dirname, '../dist/'),
    publicPath: 'http://'+os.hostname()+':8080/static/', // used by render_bundle in Django
    filename: '[name]-bundle.js',
  },
  module: {
    rules: [
      {
        test: /\.vue$/,
        loader: 'vue-loader',
      },
      {
        test: /\.pug$/,
        loader: 'pug-plain-loader',
      },
      {
        test: /\.js$/,
        loader: 'babel-loader',
        exclude: file => (
          /node_modules/.test(file) &&
          !/\.vue\.js/.test(file)
        )
      },
      {
        test: /\.css$/,
        use: [
          'vue-style-loader',
          'css-loader',
        ]
      },
      {
        test: /\.styl(us)?$/,
        use: [
          'vue-style-loader',
          'css-loader',
          'stylus-loader',
        ]
      },
      {
        test: /\.(png|jpg|gif|svg)$/,
        loader: 'url-loader',
        options: {
          limit: 10000,
          name: '[name].[ext]?[hash]',
        }
      },
    ]
  },
  optimization: {
    splitChunks: {
      cacheGroups: {
        default: false,
        vendors: {
          name: 'vendor',
          test: /[\\/]node_modules[\\/]/,
          chunks: 'all',
        },
      }
    }
  },
  plugins: [
    // magic on order
    new VueLoaderPlugin(),
    // support django-webpack-loader
    new BundleTracker({
      filename: './webpack-stats.json'
    }),
  ],
}
