"""A keyboard helper must not tab away from a control already focused."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from browser_component_dialogs import tab_to


class KeyboardHelperTests(unittest.TestCase):
    def page(self, focused=False, target_after=None):
        state=SimpleNamespace(focused=focused,presses=0)
        def press(key):
            state.presses+=1
            # Native focus can leave the page; repeatedly dispatching Tab to
            # that page is not guaranteed to cycle through browser chrome.
            state.focused=state.presses==target_after
        locator=SimpleNamespace(evaluate=lambda script: state.focused if 'document.activeElement' in script else True)
        page=SimpleNamespace(keyboard=SimpleNamespace(press=press),locator=lambda selector:locator,
            evaluate=lambda script:dict(focused='BODY',hasFocus=False,dialogs=[]),screenshot=lambda **kwargs:None)
        return page,state

    def test_existing_focus_is_checked_before_sending_tab(self):
        page,state=self.page(focused=True)
        with patch('browser_component_dialogs.reachable') as visible:
            tab_to(page,'#step-ai-apply')
        self.assertEqual(state.presses,0)
        visible.assert_called_once_with(page,'#step-ai-apply')

    def test_nonfocused_target_requires_real_key_navigation(self):
        page,state=self.page(target_after=2)
        with patch('browser_component_dialogs.reachable') as visible:
            tab_to(page,'#step-ai-apply')
        self.assertEqual(state.presses,2)
        visible.assert_called_once_with(page,'#step-ai-apply')

    def test_unreachable_target_still_fails_with_bounded_diagnostics(self):
        page,state=self.page()
        with patch('browser_component_dialogs.reachable'):
            with self.assertRaisesRegex(AssertionError,'Keyboard could not reach'):
                tab_to(page,'#step-ai-apply')
        self.assertLessEqual(state.presses,35)

    def test_existing_focus_does_not_bypass_visibility(self):
        page,state=self.page(focused=True)
        with patch('browser_component_dialogs.reachable',side_effect=AssertionError('obscured')):
            with self.assertRaisesRegex(AssertionError,'obscured'):
                tab_to(page,'#step-ai-apply')
        self.assertEqual(state.presses,0)

    def test_existing_focus_does_not_bypass_outline(self):
        page,state=self.page(focused=True)
        page.locator=lambda selector:SimpleNamespace(evaluate=lambda script:'document.activeElement' in script)
        with patch('browser_component_dialogs.reachable'):
            with self.assertRaisesRegex(AssertionError,'visible outline'):
                tab_to(page,'#step-ai-apply')
        self.assertEqual(state.presses,0)
