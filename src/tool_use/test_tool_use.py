"""Standalone tests for the calculation tool integration (no GPU, no model).

The model is replaced by scripted replies; every program run here is written in this file.
Run: python test_tool_use.py   (Python 3.11+, because the sandbox starts its child with -P)
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import loop_r2  # noqa: E402
import router  # noqa: E402
import sandbox  # noqa: E402
import scoring  # noqa: E402
import toolcall  # noqa: E402

ROW = {'instruction': 'Calcule le montant : quantité × prix unitaire + frais fixes. Deux décimales, suffixe EUR, aucun autre texte.',
       'contexte': 'Situation fictive : essai.\nQuantité : 7. Prix unitaire : 3.75 EUR. Frais fixes : 2.35 EUR.'}
CODE = 'from decimal import Decimal\nprint(Decimal("7") * Decimal("3.75") + Decimal("2.35"))'


def call_text(code):
    return f'<tool_call>\n<function=executer_python>\n<parameter=code>\n{code}\n</parameter>\n</function>\n</tool_call>'


def scripted(*texts):
    replies = iter(texts)
    return lambda messages, tools: {'text': next(replies)}


class Sandbox(unittest.TestCase):
    def test_allowed_code_runs(self):
        result = sandbox.execute(CODE)
        self.assertEqual((result['status'], result['stdout']), ('OK', '28.60'))

    def test_forbidden_module_is_refused(self):
        result = sandbox.execute('import os\nprint(os.listdir("."))')
        self.assertIn(result['status'], ('REFUSED', 'ERROR'))
        self.assertEqual(result['stdout'], '')

    def test_forbidden_builtin_is_refused(self):
        self.assertIsNotNone(sandbox.check('open("x.txt", "w").write("x")'))

    def test_no_print_is_reported(self):
        self.assertEqual(sandbox.execute('x = 1 + 1')['status'], 'NO_OUTPUT')


class Parsing(unittest.TestCase):
    def test_native_xml_call(self):
        content, calls, fmt = toolcall.parse('Je calcule.\n' + call_text('print(2 + 2)'))
        self.assertEqual(fmt, 'xml')
        self.assertEqual(calls, [{'name': 'executer_python', 'arguments': {'code': 'print(2 + 2)'}}])
        self.assertEqual(content, 'Je calcule.')

    def test_plain_answer(self):
        self.assertEqual(toolcall.parse('28.60 EUR'), ('28.60 EUR', [], 'none'))

    def test_markup_leak_is_detected(self):
        self.assertTrue(toolcall.leaked_markup('<tool_call> 28.60 EUR'))


class Router(unittest.TestCase):
    def test_calculation_request_is_routed(self):
        self.assertTrue(router.route_a('Calcule la durée en minutes entières.')[0])

    def test_writing_request_is_not_routed(self):
        self.assertFalse(router.route_a('Rédige un courriel poli pour remercier le client.')[0])

    def test_known_limit_writing_with_a_deadline_word(self):
        # Measured reserve of TOOLCALC R2: writing tasks that mention a deadline are routed too.
        self.assertTrue(router.route_a('Réponds au client au sujet du délai de livraison.')[0])


class Loop(unittest.TestCase):
    def test_one_call_then_answer(self):
        trace = loop_r2.tool_loop(ROW, scripted(call_text(CODE), '28.60 EUR'), sandbox.execute)
        self.assertEqual((trace['final_status'], trace['final'], trace['tool_rounds']), ('ANSWERED', '28.60 EUR', 1))
        self.assertEqual(trace['turns'][0]['results'][0]['stdout'], '28.60')
        self.assertEqual(loop_r2.system_answer(trace, 'direct'), ('28.60 EUR', False))

    def test_identical_retry_stops_and_falls_back(self):
        bad = 'print(1/0)'
        trace = loop_r2.tool_loop(ROW, scripted(call_text(bad), call_text(bad)), sandbox.execute)
        self.assertEqual(trace['final_status'], 'RETRY_STOPPED')
        self.assertEqual(loop_r2.system_answer(trace, '28.60 EUR'), ('28.60 EUR', True))

    def test_escaped_quotes_are_repaired_once(self):
        result = loop_r2.run_tool({'name': 'executer_python', 'arguments': {'code': 'print(\\"ok\\")'}}, sandbox.execute)
        self.assertEqual((result['status'], result['stdout'], result.get('repaired_escaped_quotes')), ('OK', 'ok', True))


class Scoring(unittest.TestCase):
    def test_final_value_versus_exact_match(self):
        s = scoring.score('Le montant est de 28.60 EUR.', '28.60 EUR')
        self.assertTrue(s['valeur_finale'])
        self.assertFalse(s['exact'])

    def test_last_value_counts(self):
        self.assertFalse(scoring.score('28.60 EUR, non : 30.95 EUR', '28.60 EUR')['valeur_finale'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
