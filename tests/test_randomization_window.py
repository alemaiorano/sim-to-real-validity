import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_randomization_window import risk_dates, primary_vectors
import compute_validity as cv


class WindowTests(unittest.TestCase):
    def test_inclusive_dates_and_cross_boundary_package(self):
        rows = [{'clickability_test_id':pid,'created_at':day+' 12:34:56.789'} for pid,day in [
            ('before','2013-06-24'),('first','2013-06-25'),('last','2014-01-10'),
            ('after','2014-01-11'),('cross','2014-01-11'),('cross','2014-01-10')]]
        out=risk_dates(rows,{'before','first','last','after','cross'})
        self.assertEqual({k for k,v in out.items() if v['in_risk_window']},{'first','last','cross'})
        with self.assertRaises(ValueError):risk_dates(rows,{'missing'})

    def test_source_date_mapping_has_canonical_serialization_order(self):
        rows = [{'clickability_test_id':pid,'created_at':'2014-01-11'} for pid in ['z','a','m']]
        self.assertEqual(list(risk_dates(rows,{'z','a','m'})),['a','m','z'])

    def test_primary_reconstruction_checks_mask_and_missingness(self):
        corpus=[{'package_id':'p','variants':[{'variant_id':'a','real_ctr':.1},{'variant_id':'b','real_ctr':.2}]}]
        scores={'p':[(.1,.2),(.2,.8)]}
        report={'primary':{arm:cv.analyze(scores,iters=2) for arm in ['panel','baseline']}}
        rows=[{'backend':'azure','package_id':'p','variant_id':v,'arm':arm,'included_primary':'1',
               'planned_n':'30','valid_n':'30','missing_n':'0','real_ctr':str(real),'mean':str(pred)}
              for arm in ['panel','baseline'] for v,real,pred in [('a',.1,.2),('b',.2,.8)]]
        self.assertEqual(primary_vectors(corpus,report,rows,'azure')['panel'],scores)
        rows[0]['valid_n']='29'
        with self.assertRaises(ValueError):primary_vectors(corpus,report,rows,'azure')
        rows[0]['valid_n']='30';rows[0]['included_primary']='0'
        with self.assertRaises(ValueError):primary_vectors(corpus,report,rows,'azure')
