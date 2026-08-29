module.exports = {
  ci: {
    collect: {
      staticDistDir: './build/public-site',
      numberOfRuns: 1,
      url: [
        'http://localhost/',
        'http://localhost/download/',
        'http://localhost/support/',
        'http://localhost/guide/',
        'http://localhost/releases/',
        'http://localhost/accessibility/'
      ]
    },
    assert: {
      assertions: {
        'categories:accessibility': ['error', { minScore: 1 }],
        'categories:best-practices': ['error', { minScore: 0.95 }],
        'categories:seo': ['error', { minScore: 0.9 }],
        'categories:performance': ['error', { minScore: 0.9 }]
      }
    },
    upload: {
      target: 'filesystem',
      outputDir: './build/lighthouse'
    }
  }
};
