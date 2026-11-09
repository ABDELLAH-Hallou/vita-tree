import difflib
import hashlib
import unittest

from vita_tree.factual_contract import resolve_document, validate


def report(before, after, step='adapt'):
    old = before.removesuffix('\n').split('\n') if before else []
    new = after.removesuffix('\n').split('\n') if after else []
    changes = []
    for tag, start, end, out_start, out_end in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag == 'equal':continue
        changes.append({'id': 'change-'+hashlib.sha256(str(len(changes)).encode()).hexdigest(),
                        'operation': tag, 'original': '\n'.join(old[start:end]), 'proposed': '\n'.join(new[out_start:out_end]),
                        'kind': 'semantic_or_factual', 'reason': 'unverified_semantic_change',
                        'verification': 'confirmation_required', 'source_fact_ids': [],
                        'output_span': {'line_start': out_start+1, 'line_end': out_end} if out_end > out_start else None})
    return {'contract_version': 'factual-changes/1', 'step': step, 'revision': 'fc-'+'a'*64,
            'status': 'confirmation_required', 'application_status': 'not_applied',
            'document': after, 'target_before': before, 'source_facts': [], 'changes': changes,
            'candidate_sources': {'sources': [{'kind': 'cv', 'content': before}]}}


class FactualContractTests(unittest.TestCase):
    def choices(self, value, action):
        return [{'id': item['id'], 'action': action} for item in value['changes']]

    def test_mixed_positional_decisions_keep_repeated_text_and_handle_insert_delete(self):
        value = report('same\nold\nsame\nremove\nend\n', 'same\nnew\nsame\nend\nadded\n')
        decisions = self.choices(value, 'accept')
        decisions[0]['action'] = 'reject'
        decisions[1]['action'] = 'reject'
        decisions[2].update(action='edit', text='edited\nextra')
        actual, omitted = resolve_document(value, decisions)
        self.assertEqual(actual, 'same\nold\nsame\nremove\nend\nedited\nextra\n')
        self.assertFalse(omitted)

    def test_accept_and_reject_retain_exact_document_and_terminal_newlines(self):
        value = report('old\n', 'new')
        self.assertEqual(resolve_document(value, self.choices(value, 'accept')), ('new', False))
        self.assertEqual(resolve_document(value, self.choices(value, 'reject')), ('old\n', False))
        value = report('a\nold\nb\n', 'a\n\nb\n')
        choice = self.choices(value, 'edit');choice[0]['text']=''
        self.assertEqual(resolve_document(value, choice)[0], 'a\nb\n')

    def test_rejecting_whole_letter_preserves_previous_target_instead_of_copying_cv(self):
        value = report('source CV', 'proposed letter', 'cover')
        value['target_before'] = None
        self.assertEqual(resolve_document(value, self.choices(value, 'reject')), (None, True))
        value['target_before'] = 'previous letter'
        self.assertEqual(resolve_document(value, self.choices(value, 'reject')), ('previous letter', True))

    def test_missing_duplicate_unknown_actions_or_ids_and_changed_host_diff_fail(self):
        value = report('a\nb\nc', 'A\nb\nC')
        choices = self.choices(value, 'accept')
        for invalid in ([], [choices[0]]*2, [{**choices[0], 'action': 'approve'}, choices[1]],
                        [{**choices[0], 'id': 'unknown'}, choices[1]], [{**choices[0], 'action': 'edit', 'text': None}, choices[1]]):
            with self.assertRaises(ValueError):resolve_document(value, invalid)
        value['changes'][0]['original'] = 'wrong original'
        choices[0]['action'] = 'reject'
        with self.assertRaisesRegex(ValueError, 'host diff'):resolve_document(value, choices)
        with self.assertRaises(ValueError):validate({**value, 'contract_version': 'factual-changes/2'})


if __name__ == '__main__':unittest.main()
