const merge = require('webpack-merge')

const base = require('./webpack.base')

module.exports = merge(base, {
  mode: 'development',
  devtool: 'eval-source-map',
  resolve: {
    alias: {
      // use the full build to allow for template compilation
      'vue$': 'vue/dist/vue.esm.js',
    }
  },
  devServer: {
    // NOTE: This is an explicit security risk.
    disableHostCheck: true,
    headers: {
      'Access-Control-Allow-Origin': '*',
    },
    historyApiFallback: true,
  },
})
