module.exports = {
  module: {
    rules: [
      {
        test: /node_modules\/@mediapipe\/tasks-vision/,
        use: ['source-map-loader'],
        enforce: 'pre',
        parser: { javascript: { requireEnsure: false, exprContextCritical: false } }
      }
    ]
  },

  ignoreWarnings: [
    {
      module: /node_modules\/@mediapipe\/tasks-vision/,
      message: /Failed to parse source map/
    }
  ]
};
