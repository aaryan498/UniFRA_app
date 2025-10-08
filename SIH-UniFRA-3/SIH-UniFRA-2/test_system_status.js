// Simple test to verify SystemStatus component functionality
const puppeteer = require('puppeteer');

async function testSystemStatus() {
  const browser = await puppeteer.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    
    // Navigate to the application
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });
    
    // Wait for the page to load
    await page.waitForTimeout(3000);
    
    // Check if we can find system status related elements
    const hasSystemStatusPage = await page.evaluate(() => {
      return document.querySelector('[data-testid="system-status-page"]') !== null;
    });
    
    console.log('System Status Page found:', hasSystemStatusPage);
    
    // Check for performance chart
    const hasPerformanceChart = await page.evaluate(() => {
      return document.querySelector('.performance-chart') !== null;
    });
    
    console.log('Performance Chart found:', hasPerformanceChart);
    
    // Check for system logs
    const hasSystemLogs = await page.evaluate(() => {
      return document.querySelector('[data-testid="system-logs"]') !== null;
    });
    
    console.log('System Logs found:', hasSystemLogs);
    
    // Take a screenshot for verification
    await page.screenshot({ path: '/tmp/system_status_test.png', fullPage: true });
    console.log('Screenshot saved to /tmp/system_status_test.png');
    
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await browser.close();
  }
}

testSystemStatus();