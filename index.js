const express = require('express');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

const app = express();
const PORT = process.env.PORT || 10000;

app.get('/solve-cloud', async (req, res) => {
    const url = req.query.url;
    if (!url) return res.status(400).json({ error: "URL missing" });

    let browser = null;
    try {
        console.log(`🚀 Opening: ${url}`);
        
        // Browser Setup
        browser = await puppeteer.launch({
            headless: "new",
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ],
            executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || null
        });

        const page = await browser.newPage();
        
        // Stealth Settings
        await page.setViewport({ width: 1920, height: 1080 });
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

        // 1. Visit HubCloud
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });

        // 2. Wait for Cloudflare (Just a moment...)
        console.log("⏳ Waiting for Cloudflare...");
        await page.waitForFunction(() => !document.title.includes("Just a moment"), { timeout: 30000 });

        // 3. Find & Click Download Button
        console.log("🔍 Looking for button...");
        await page.waitForSelector('#download', { timeout: 15000 });
        
        // Get the link just in case click fails
        const redirectLink = await page.$eval('#download', el => el.href);
        console.log(`🔗 Found Redirect: ${redirectLink}`);

        // Click it
        await Promise.all([
            page.click('#download'),
            page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => console.log("Navigation timeout, continuing..."))
        ]);

        // 4. Wait for Final Page Redirect
        console.log("🔄 Waiting for redirects...");
        await new Promise(r => setTimeout(r, 10000)); // 10 sec wait
        
        // 5. Extract Links
        const content = await page.content();
        const currentUrl = page.url();
        console.log(`📄 Final Page: ${currentUrl}`);

        // Regex for Links
        const linkRegex = /https?:\/\/[^\s"'<>]+/g;
        const allLinks = content.match(linkRegex) || [];

        // Filters
        const keep = ["r2.dev", "fsl-lover.buzz", "fsl-cdn-1.sbs", "fukggl.buzz"];
        const ignore = ["pixeldrain", "hubcdn", "workers.dev", ".zip"];

        const finalLinks = [...new Set(allLinks)].filter(link => {
            return keep.some(k => link.includes(k)) && !ignore.some(i => link.includes(i));
        });

        res.json({
            status: "success",
            total: finalLinks.length,
            final_links: finalLinks
        });

    } catch (error) {
        console.error(error);
        res.status(500).json({ status: "error", message: error.message });
    } finally {
        if (browser) await browser.close();
    }
});

app.listen(PORT, () => {
    console.log(`Listening on port ${PORT}`);
});
