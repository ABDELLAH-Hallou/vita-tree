import unittest

from vita_tree.workflow import clean_stages, plan, transition


class WorkflowHistoryTests(unittest.TestCase):
    def test_selection_is_explicit_validated_and_ordered(self):
        stages = plan({'steps': ['cover', 'analyze']}, {'cover': True})
        self.assertEqual([s['id'] for s in stages if s['status'] == 'pending'], ['analyze', 'cover', 'validating'])
        for options in ({'steps': []}, {'steps': 'review'}, {'steps': [None]}, {'steps': ['analyze', 'analyze']},
                        {'steps': ['unknown']}, {'steps': ['analyze'], 'cover': True}, {'steps': ['review']}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                plan(options, {})

    def test_restart_retains_completed_steps_and_blocks_dependencies(self):
        stages = plan({'extract': True, 'review': True}, {'extract': True, 'review': True})
        stages = transition(stages, step='extract')
        stages = transition(stages, step='analyze')
        stages = transition(stages, terminal='interrupted')
        states = {stage['id']: stage['status'] for stage in stages}
        self.assertEqual(states, {'extract': 'succeeded', 'analyze': 'interrupted',
                                 'adapt': 'blocked', 'review': 'blocked', 'cover': 'skipped', 'validating': 'blocked'})

    def test_history_does_not_expose_additional_fields(self):
        raw = [{'id': 'analyze', 'status': 'succeeded', 'startedAt': 1, 'finishedAt': 2,
                'prompt': 'private context', 'credentials': 'private value'}]
        self.assertEqual(clean_stages(raw), [{'id': 'analyze', 'status': 'succeeded', 'startedAt': 1, 'finishedAt': 2}])
        self.assertEqual(clean_stages(None), [])

    def test_damaged_history_is_rejected(self):
        for value in ('oops', [None], [{'id': 'secret', 'status': 'running'}],
                      [{'id': 'analyze', 'status': 'running', 'startedAt': 'private-value'}],
                      [{'id': 'analyze', 'status': 'running'}] * 2):
            with self.subTest(value=value), self.assertRaises(ValueError):
                clean_stages(value)
