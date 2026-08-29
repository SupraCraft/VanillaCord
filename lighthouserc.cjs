const baseURL = 'http://127.0.0.1:4174';

module.exports = {
  ci: {
    collect: {
      startServerCommand: `python3 scripts/build-public-site.py --output build/public-site --base-url ${baseURL}/ && python3 -u -m http.server 4174 --directory build/public-site --bind 127.0.0.1`,
      startServerReadyPattern: 'Serving HTTP on',
      startServerReadyTimeout: 120000,
      numberOfRuns: 1,
      url: [
        `${baseURL}/`,
        `${baseURL}/download/`,
        `${baseURL}/support/`,
        `${baseURL}/guide/`,
        `${baseURL}/releases/`,
        `${baseURL}/accessibility/`
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
