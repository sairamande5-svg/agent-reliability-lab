"""Optional Playwright browser acceptance check; runtime app needs no dependencies."""
import argparse
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from threading import Thread

from playwright.sync_api import sync_playwright
from agentlab.dashboard import Handler, publish


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screenshot', type=Path)
    args = parser.parse_args()
    with TemporaryDirectory() as directory:
        output = Path(directory)
        publish(output, 'reference')
        report = publish(output, 'candidate')
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, report=report))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as p:
                installed = shutil.which('chromium')
                browser = p.chromium.launch(**({'executable_path': installed} if installed else {}), args=['--no-sandbox'])
                try:
                    page = browser.new_page(viewport={'width':1440,'height':1100})
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.goto(f'http://127.0.0.1:{server.server_port}')
                    assert page.locator('.scenario').count() == 12
                    assert page.locator('#active-run option').count() == 2
                    page.select_option('#active-run', 'reference')
                    page.select_option('#reference-run', 'candidate')
                    assert '0' in page.locator('#comparison').inner_text()
                    page.select_option('#outcome','fail')
                    assert page.locator('.scenario').count() == 7
                    page.click('#jump')
                    assert page.locator('.scenario').count() == 1
                    page.click('summary')
                    assert 'replayed_action' in page.locator('pre').inner_text()
                    with page.expect_download() as download:
                        page.click('#download')
                    assert download.value.suggested_filename == 'agent-reliability-evidence.json'
                    page.select_option('#suite','replay')
                    assert page.locator('.scenario').count() == 4
                    page.select_option('#outcome','fail')
                    assert page.locator('.scenario').count() == 2
                    page.select_option('#suite','support')
                    page.select_option('#outcome','all')
                    assert page.locator('.scenario').count() == 4
                    if args.screenshot:
                        args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(args.screenshot), full_page=True)
                    page.set_viewport_size({'width':390,'height':844})
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    assert not errors, errors
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
    print('Browser acceptance passed: saved runs, comparison, filtering, recovery evidence, replay failures, download, mobile layout.')


if __name__ == '__main__':
    main()
