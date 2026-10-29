"""Explicit engines: Playwright WebKit is not a claim about shipping Safari."""
from pathlib import Path

BROWSERS = ('chrome', 'chromium', 'firefox', 'webkit')


def launch_browser(playwright, name):
    if name not in BROWSERS:
        raise ValueError('Unsupported test browser')
    return (playwright.chromium.launch(channel='chrome') if name == 'chrome'
            else getattr(playwright, name).launch())


def tab_to(page, selector, reachable):
    """Duck-typed navigation: unit tests need no Playwright installation."""
    history=[]
    for attempt in range(36):
        if page.locator(selector).evaluate('(el) => el===document.activeElement'):
            reachable(page, selector)
            assert page.locator(selector).evaluate('''el=>{const s=getComputedStyle(el);return parseFloat(s.outlineWidth)>=1&&s.outlineStyle!=='none';}'''), 'Focused action has no visible outline'
            return
        if attempt<35:
            history.append(page.evaluate('document.activeElement.id||document.activeElement.tagName'))
            page.keyboard.press('Tab')
    state=page.evaluate('''()=>({focused:document.activeElement.id||document.activeElement.tagName,
      hasFocus:document.hasFocus(),dialogs:[...document.querySelectorAll('dialog[open]')].map(el=>el.id)})''')
    page.screenshot(path=str(Path('.test-artifacts')/'component-keyboard-failure.png'))
    raise AssertionError('Keyboard could not reach ' + selector + '; state=' + str(state) + '; history=' + str(history))
