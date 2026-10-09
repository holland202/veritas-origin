"""ITC-001 post-hoc compute audit: actual masked execution, not simulated savings."""
from __future__ import annotations
import importlib.util
import pathlib
import sys
import unittest
import numpy as np

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"/"origin"))
sys.path.insert(0,str(ROOT/"tools"))
import itc001 as origin
import measure_itc001_compute as compute

class RuntimeControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.theta=origin.initialize(20261161)
        bits=np.random.default_rng(38).integers(0,2,size=(120,16),dtype=np.int64)
        tasks=np.arange(120,dtype=np.int64)%6
        cls.x=origin.encode(bits,tasks)
        cls.tasks=tasks

    def test_actual_masked_output_matches_counterfactual_depth_choices(self):
        _,logits=origin.forward(self.theta,self.x)
        probs=origin.stable_prob(logits)
        output,depth=compute.run_adaptive_masked(self.theta,self.x)
        # Public reference halting criterion, independent of labels.
        expected=np.full(len(self.x),5,dtype=np.int64)
        for t in (2,3,4):
            good=(np.abs(probs[t-1]-.5)>=.18)&(
                np.abs(probs[t-1]-probs[t-2])<=.08)
            expected[(expected==5)&good]=t
        self.assertTrue(np.array_equal(depth,expected))
        self.assertTrue(np.allclose(output,
            probs[depth-1,np.arange(len(depth))],rtol=0,atol=1e-12))

    def test_fixed_depth_compute_matches_saved_five_steps(self):
        _,logits=origin.forward(self.theta,self.x)
        for depth in (1,2,3,5):
            got=compute.run_dense(self.theta,self.x,depth)
            self.assertTrue(np.allclose(got,
                origin.stable_prob(logits[depth-1]),rtol=0,atol=1e-12))

    def test_actual_masks_never_overspend_five_passes(self):
        _,depth=compute.run_adaptive_masked(self.theta,self.x)
        self.assertTrue(np.all((depth>=2)&(depth<=5)))
        self.assertLessEqual(int(np.sum(depth)),5*len(depth))

    def test_no_oracle_label_appears_in_runtime_interface(self):
        import ast
        source=ast.parse((ROOT/"tools/measure_itc001_compute.py").read_text())
        function=next(node for node in source.body
            if isinstance(node,ast.FunctionDef) and
            node.name=="run_adaptive_masked")
        params=[a.arg for a in function.args.args]
        self.assertEqual(params,["theta","features"])
        self.assertNotIn("labels",ast.unparse(function))
        self.assertNotIn("target",ast.unparse(function))

    def test_invalid_benchmark_repetition_refused(self):
        for count in (0,31,-1,1.5,True):
            with self.assertRaises(ValueError):
                compute.benchmark({"seed_records":[]},count)

    def test_nonvacuous_output_shape(self):
        out,depth=compute.run_adaptive_masked(self.theta,self.x)
        self.assertEqual(out.shape,(120,))
        self.assertEqual(depth.shape,(120,))
        self.assertTrue(np.all(np.isfinite(out)))
        self.assertTrue(np.all((out>=0)&(out<=1)))

if __name__=="__main__":unittest.main()
