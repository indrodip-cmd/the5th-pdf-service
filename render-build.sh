#!/usr/bin/env bash
set -e
npm install
node -e "const p = require('puppeteer/install.js'); if(typeof p === 'function') p();" 2>/dev/null || npx puppeteer browsers install chrome
