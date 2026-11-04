import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/tamil/.gemini/ai-company/tools/doc-pdf/node_modules/playwright');

const sessions = JSON.parse(fs.readFileSync('CRM_Integrated_v2/CRM/scratch/sessions.json', 'utf8'));
const outDir = path.resolve('docs/project-docs/screenshots');

async function main() {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });

  // 1. Login Screen (Unauthenticated)
  console.log('Capturing Login screen...');
  const ctxAnon = await browser.newContext({ viewport: { width: 1366, height: 768 } });
  const pAnon = await ctxAnon.newPage();
  await pAnon.goto('http://127.0.0.1:8000/login/', { waitUntil: 'networkidle' });
  await pAnon.screenshot({ path: path.join(outDir, '01_login_screen.png'), fullPage: false });
  await ctxAnon.close();

  // Helper for authenticated session
  async function captureWithSession(role, url, filename, viewport = { width: 1366, height: 768 }) {
    console.log(`Capturing ${filename} (${role}) -> ${url}...`);
    const ctx = await browser.newContext({ viewport });
    await ctx.addCookies([{
      name: 'sessionid',
      value: sessions[role],
      domain: '127.0.0.1',
      path: '/',
      httpOnly: true,
      secure: false,
      sameSite: 'Lax'
    }]);
    const page = await ctx.newPage();
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
      await page.waitForTimeout(1000); // Wait for UI rendering
      await page.screenshot({ path: path.join(outDir, filename), fullPage: false });
      console.log(`Saved ${filename}`);
    } catch (err) {
      console.error(`Failed capturing ${url}:`, err.message);
    }
    await ctx.close();
  }

  // 2. Admin Dashboard (Desktop)
  await captureWithSession('admin', 'http://127.0.0.1:8000/admin/dashboard/', '01_admin_dashboard.png');

  // 3. Admin Dashboard (Mobile 390px)
  await captureWithSession('admin', 'http://127.0.0.1:8000/admin/dashboard/', '01_mobile_dashboard.png', { width: 390, height: 844 });

  // 4. Leads List / Pipeline
  await captureWithSession('admin', 'http://127.0.0.1:8000/leads/', '02_leads_pipeline.png');

  // 5. Enrollments List
  await captureWithSession('admin', 'http://127.0.0.1:8000/enrollments/', '04_enrollments_list.png');

  // 6. Accountant Verification
  await captureWithSession('admin', 'http://127.0.0.1:8000/accountant/verification/', '04_accountant_verification.png');

  // 7. Tax Invoice / Receipt View
  await captureWithSession('admin', 'http://127.0.0.1:8000/enrollments/receipt/63/', '04_tax_invoice.png');

  // 8. Counselor Workspace
  await captureWithSession('counselor', 'http://127.0.0.1:8000/counselor/workspace/', '08_counselor_workspace.png');

  // 9. Telecaller Workspace
  await captureWithSession('telecaller', 'http://127.0.0.1:8000/telecaller/workspace/', '08_telecaller_workspace.png');

  // 10. Email Logs List
  await captureWithSession('admin', 'http://127.0.0.1:8000/admin/email-logs/', '09_email_logs.png');

  await browser.close();
  console.log('All screenshots captured successfully!');
}

main().catch(err => {
  console.error('Fatal screenshot error:', err);
  process.exit(1);
});
