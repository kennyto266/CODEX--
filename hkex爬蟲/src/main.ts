// For more information, see https://crawlee.dev/
import { PlaywrightCrawler, ProxyConfiguration } from 'crawlee';
import fs from 'fs';
import path from 'path';

import { router } from './routes.js';

const startUrls = ['https://www.hkex.com.hk/chi/stat/smstat/dayquot/qtn_c.asp'];

const crawler = new PlaywrightCrawler({
    // proxyConfiguration: new ProxyConfiguration({ proxyUrls: ['...'] }),
    requestHandler: router,
    maxRequestsPerCrawl: 1,
});

await crawler.run(startUrls);
