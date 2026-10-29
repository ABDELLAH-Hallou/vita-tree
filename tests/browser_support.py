"""Explicit engines: Playwright WebKit is not a claim about shipping Safari."""
BROWSERS = ('chrome', 'chromium', 'firefox', 'webkit')


def launch_browser(playwright, name):
    if name not in BROWSERS:
        raise ValueError('Unsupported test browser')
    return (playwright.chromium.launch(channel='chrome') if name == 'chrome'
            else getattr(playwright, name).launch())
