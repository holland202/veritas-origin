"""ITC-001 positive and adversarial experiments; original records remain untouched."""
from __future__ import annotations
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"/"origin"))
sys.path.insert(0,str(ROOT/"tools"))
import itc001 as producer
import verify_itc001 as independent

class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact=producer.run()

    def test_full_public_roster(self):
        self.assertEqual(self.artifact['registered_constants']['seeds'],list(range(20261161,20261167)))
        self.assertEqual(len(self.artifact['seed_records']),6)
        self.assertEqual(self.artifact['registered_constants']['trainable_parameters'],1153)

    def test_actual_gradients_with_finite_differences(self):
        p=producer.initialize(20261161)
        rng=np.random.default_rng(23)
        x,y,_=producer.draw_train_batch(rng)
        value,grads,_,_=producer.loss_and_grad(p,x[:9],y[:9])
        self.assertGreater(value,0)
        for key,ind in [('Win',(3,2)),('Wr',(3,3)),('bias',(5,)),('Wout',(7,0)),('bout',(0,))]:
            step=1e-5
            q=p[key][ind]
            p[key][ind]=q+step
            hi=producer.loss_and_grad(p,x[:9],y[:9])[0]
            p[key][ind]=q-step
            lo=producer.loss_and_grad(p,x[:9],y[:9])[0]
            p[key][ind]=q
            self.assertAlmostEqual(float(grads[key][ind]),(hi-lo)/(2*step),delta=2e-7)

    def test_genuine_latent_state_change(self):
        p=producer.initialize(20261161)
        x,_,_=producer.draw_train_batch(np.random.default_rng(7))
        states,logits=producer.forward(p,x)
        self.assertEqual(len(states),6)
        self.assertFalse(np.allclose(states[1],states[5]))
        self.assertEqual(logits.shape,(5,96))

    def test_train_and_test_patterns_exclusive(self):
        reserved=producer.test_split()
        self.assertGreater(np.sum(reserved),0)
        self.assertLess(np.sum(reserved),65536)
        a,_,bits=producer.draw_train_batch(np.random.default_rng(11))
        b,_,_,tbits=producer.draw_test(20261161)
        self.assertTrue(np.all(~reserved[producer.bits_code(bits)]))
        self.assertTrue(np.all(reserved[producer.bits_code(tbits)]))
        self.assertFalse(set(producer.bits_code(bits))&set(producer.bits_code(tbits)))

    def test_trainable_parameters_changed(self):
        entry=self.artifact['seed_records'][0]
        self.assertNotEqual(entry['initial_parameters_sha256'],entry['final_weights_sha256'])
        self.assertEqual(len(entry['final_weights']['Win']),22)

    def test_prediction_never_oracle_for_halting(self):
        import ast
        tree=ast.parse(Path(producer.__file__).read_text())
        body=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='policies')
        source=ast.unparse(body)
        self.assertIn('np.abs(current - 0.5)',source)
        self.assertIn('np.abs(current - previous)',source)
        self.assertNotIn('oracle',source.lower())

    def test_stopping_is_bounded_and_not_constant(self):
        for run in self.artifact['seed_records']:
            steps=np.array(run['selected_depths'])
            self.assertTrue(np.all((steps>=2)&(steps<=5)))
            self.assertGreater(len(np.unique(steps)),1)
            self.assertGreater(run['policy_results']['adaptive']['early_stop_count'],0)

    def test_matched_budget_within_each_task(self):
        for run in self.artifact['seed_records']:
            adaptive=run['policy_results']['adaptive']
            shuffle=run['policy_results']['shuffle_task']
            self.assertEqual(adaptive['passes_by_task'],shuffle['passes_by_task'])
            self.assertEqual(adaptive['mean_passes'],shuffle['mean_passes'])
            self.assertEqual(sum(adaptive['depth_histogram']),3072)

    def test_wrong_early_decisions_retained_not_clean_label(self):
        count=sum(r['policy_results']['adaptive']['early_incorrect_count']
                  for r in self.artifact['seed_records'])
        self.assertGreater(count,0)
        self.assertEqual(count,sum(sum(r['policy_results']['adaptive']['early_incorrect_by_task'])
                                   for r in self.artifact['seed_records']))

    def test_nonvacuous_correct_and_wrong_examples(self):
        for run in self.artifact['seed_records']:
            self.assertGreater(run['policy_results']['fixed5']['wrong_predictions'],0)
            self.assertLess(run['policy_results']['fixed5']['wrong_predictions'],3072)

    def test_hard_task_still_measured(self):
        for run in self.artifact['seed_records']:
            tasks=run['test_task_ids']
            self.assertEqual([tasks.count(i) for i in range(6)],[512]*6)
            self.assertEqual(len(run['test_targets']),3072)

    def test_hypothesis_status_preserves_both_possible_verdicts(self):
        self.assertIn(self.artifact['aggregate']['H1'],(
            'H1_EXPLORATORY_THRESHOLD_MET_NOT_VALIDATED','H1_NOT_SUPPORTED'))
        self.assertIn(self.artifact['aggregate']['H2'],(
            'H2_EXPLORATORY_THRESHOLD_MET_NOT_VALIDATED','H2_NOT_SUPPORTED'))

    def test_unique_write_never_overwrites(self):
        with tempfile.TemporaryDirectory() as t:
            f,s=producer.save_new(self.artifact,Path(t))
            g,h=producer.save_new(self.artifact,Path(t))
            self.assertNotEqual(f,g)
            self.assertEqual(s,h)
            self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),s)

    def test_no_training_without_optin(self):
        with self.assertRaises(SystemExit):producer.main([])

class IndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.fixture=producer.run()

    def raw(self,obj):return json.dumps(obj,sort_keys=True,allow_nan=False).encode()
    def replay(self,obj):
        blob=self.raw(obj)
        return independent.verify(blob,hashlib.sha256(blob).hexdigest())
    def mutate(self,callback,description):
        payload=copy.deepcopy(self.fixture)
        callback(payload)
        with self.assertRaisesRegex(ValueError,description):self.replay(payload)

    def test_complete_numerical_positive(self):
        result=self.replay(self.fixture)
        self.assertEqual(result['total_test_decisions'],18432)
        self.assertEqual(result['verdict'],'INDEPENDENT_NUMERICAL_REPLAY_CONSISTENT_ONLY')

    def test_wrong_outer_digest(self):
        raw=self.raw(self.fixture)
        with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):
            independent.verify(raw,'0'*64)

    def test_rehashed_changed_weight(self):
        self.mutate(lambda d:d['seed_records'][0]['final_weights']['Win'][0].__setitem__(0,999.0),
                    'learned weights mismatch')

    def test_rehashed_changed_prediction(self):
        self.mutate(lambda d:d['seed_records'][0]['probabilities_by_depth'][1].__setitem__(0,.001),
                    'numeric replay mismatch')

    def test_rehashed_oracle_label(self):
        self.mutate(lambda d:d['seed_records'][0]['test_targets'].__setitem__(0,2),
                    'withheld bits codes|test targets')

    def test_rehashed_forged_halt_depth(self):
        self.mutate(lambda d:d['seed_records'][0]['selected_depths'].__setitem__(0,1),
                    'halting decision')

    def test_rehashed_forged_hypothesis(self):
        self.mutate(lambda d:d['aggregate'].__setitem__('H2','H2_VALIDATED'),
                    'registered summary')

    def test_rehashed_misreported_budget(self):
        self.mutate(lambda d:d['seed_records'][0]['policy_results']['shuffle_task']
                     ['passes_by_task'].__setitem__(0,0),
                    'matched stopping policy outcomes')

    def test_missing_seed(self):
        self.mutate(lambda d:d['seed_records'].pop(),'missing seed record')

    def test_injected_future_task(self):
        self.mutate(lambda d:d['registered_constants']['seeds'].append(99999),
                    'constants')

    def test_false_validation_status(self):
        self.mutate(lambda d:d.__setitem__('status','VALIDATED'),
                    'attempted validation promotion')

    def test_duplicate_json_keys(self):
        raw=b'{"claim":1,"claim":2}'
        with self.assertRaisesRegex(ValueError,'duplicate JSON keys'):
            independent.verify(raw,hashlib.sha256(raw).hexdigest())

    def test_nonfinite_json(self):
        raw=b'{"x":NaN}'
        with self.assertRaisesRegex(ValueError,'nonfinite JSON'):
            independent.verify(raw,hashlib.sha256(raw).hexdigest())

    def test_independent_verifier_does_not_import_runner(self):
        import ast
        tree=ast.parse(Path(independent.__file__).read_text())
        imports=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imports.extend(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom):imports.append(node.module or '')
        self.assertNotIn('itc001',imports)
        self.assertNotIn('src.origin.itc001',imports)

if __name__=='__main__':unittest.main()
