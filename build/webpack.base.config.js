const os = require('os')
const path = require('path')
const vueConfig = require('./vue-loader.config')

module.exports = {
  context: path.resolve(__dirname, '../'),
  devtool: '#eval-source-map',
  entry: {
    app: './src/main.js',
    vendor: ['axios', 'vue', 'vue-router', 'vue-touch']
  },
  output: {
    path: path.resolve(__dirname, '../dist/'),
    publicPath: 'http://'+os.hostname()+':8080/static/', // used by render_bundle in Django
    filename: 'app-bundle.js'
  },
  module: {
    rules: [
      {
        test: /\.vue$/,
        loader: 'vue',
        options: vueConfig
      },
      {
        test: /\.js$/,
        loader: 'babel-loader',
        exclude: /node_modules/
      },
      {
        test: /\.(png|jpg|gif|svg)$/,
        loader: 'url',
        options: {
          limit: 10000,
          name: '[name].[ext]?[hash]'
        }
      }
    ]
  },
  devServer: {
    historyApiFallback: true,
    noInfo: false
  }
}
