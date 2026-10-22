// shot.mjs - the eyes of an AI agent.
//
//   npm i playwright
//   node tools/shot.mjs ru/01.html
//
// Opens a page the way a phone shows it, reports anything that runs past the
// edge and saves a screenshot: the model reads files, it does not see pages.
// Exits 1 on overflow and 0 when the page is clean, so it can be used as a
// check and not only by hand.
//
// Install playwright in this project, not above it: node resolves modules
// upwards and will happily find someone else's copy, and then the error talks
// about a missing browser instead of a misplaced install.

const file = process.argv[2] || 'index.html';

let chromium;
try {
  ({ chromium } = await import('playwright'));
} catch {
  console.error('playwright не найден. Поставьте его в этой папке:');
  console.error('    npm init -y');
  console.error('    npm i playwright');
  console.error('    npx playwright install chromium chromium-headless-shell');
  process.exit(2);
}

// The argument can be a URL, a relative file name or an absolute path.
const url = file.startsWith('http') ? file
  : 'file://' + (file.startsWith('/') ? file : process.cwd() + '/' + file);

let browser;
try {
  browser = await chromium.launch();
} catch (e) {
  console.error('браузер не запустился: ' + String(e.message).split('\n')[0]);
  console.error('если написано "Executable doesn\'t exist" - браузер не скачан:');
  console.error('    npx playwright install chromium chromium-headless-shell');
  console.error('если написано "error while loading shared libraries" - не хватает системных библиотек:');
  console.error('    установка библиотек требует прав администратора.');
  process.exit(2);
}

const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
await page.goto(url);

// Everything is measured inside the page: this runs in the browser.
const report = await page.evaluate(() => {
  const viewport = document.documentElement.clientWidth;
  const overflowing = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.right > viewport + 1) overflowing.push(el.tagName + ': ' + el.textContent.trim().slice(0, 30));
  }
  return { viewport, pageWidth: document.documentElement.scrollWidth, overflowing };
});

console.log('экран телефона: ' + report.viewport + 'px, страница: ' + report.pageWidth + 'px');
console.log(report.overflowing.length ? 'за край вылезло: ' + report.overflowing.length : 'за край ничего не вылезло');
for (const el of report.overflowing.slice(0, 5)) console.log('  ' + el);

await page.screenshot({ path: 'phone.png', fullPage: true });
console.log('снимок: phone.png - посмотрите на него своими глазами');

await browser.close();
process.exit(report.overflowing.length ? 1 : 0);
