"""Post-hoc period-exclusion sensitivity; never mutate frozen primary reports."""
import argparse
import csv
from datetime import date
import hashlib
import json
import math
from pathlib import Path

from analysis_io import write_json
import compute_validity as cv

START = date(2013, 6, 25)
END = date(2014, 1, 10)
SOURCE = 'https://doi.org/10.1038/s41597-024-03600-w'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def risk_dates(rows, package_ids):
    """Use original naive calendar dates; archive timezone is undocumented."""
    dates = {pid: set() for pid in sorted(package_ids)}
    for row in rows:
        pid = row['clickability_test_id'].strip()
        if pid in dates:
            dates[pid].add(date.fromisoformat(row['created_at'][:10]))
    if any(not ds for ds in dates.values()):
        raise ValueError('missing source date for a corpus package')
    return {pid: {'min_date': min(ds).isoformat(), 'max_date': max(ds).isoformat(),
                  'in_risk_window': any(START <= day <= END for day in ds)}
            for pid, ds in dates.items()}


def primary_vectors(corpus, report, rows, backend):
    ids = set(report['primary']['panel']['package_ids'])
    if ids != set(report['primary']['baseline']['package_ids']):
        raise ValueError('primary arms must share complete package coverage')
    observations = {}
    for row in rows:
        if row['backend'] != backend:
            raise ValueError('wrong backend')
        if (row['included_primary'] == '1') != (row['package_id'] in ids):
            raise ValueError('changed primary mask')
        key = row['package_id'], row['variant_id'], row['arm']
        if key in observations:
            raise ValueError('duplicate variant arm')
        observations[key] = row
    result = {'panel': {}, 'baseline': {}}
    for package in corpus:  # Preserve original package and variant order for seeded bootstrap.
        pid = package['package_id']
        if pid not in ids:
            continue
        for arm in result:
            scores = []
            for variant in package['variants']:
                row = observations[pid, variant['variant_id'], arm]
                if int(row['planned_n']) != 30 or int(row['valid_n']) != 30 or int(row['missing_n']):
                    raise ValueError('primary package has missing planned observations')
                if not math.isclose(float(row['real_ctr']), variant['real_ctr'], abs_tol=1e-15, rel_tol=1e-12):
                    raise ValueError('changed ground truth')
                scores.append((variant['real_ctr'], float(row['mean'])))
            result[arm][pid] = scores
    if set(result['panel']) != ids:
        raise ValueError('unknown primary package')
    for arm, packages in result.items():
        check = cv.analyze(packages, iters=2)
        for metric in cv.METRICS:
            expected = report['primary'][arm][metric]
            for field in ['mean', 'n_total', 'n_valid', 'n_undefined', 'valid_package_ids']:
                if check[metric][field] != expected[field]:
                    raise ValueError('reconstructed primary differs: ' + arm + '/' + metric + '/' + field)
    return result


def analyze(run, derived):
    run, derived = Path(run), Path(derived)
    plan = json.loads((run / 'plan.json').read_text())
    for name, expected in plan['input_sha256'].items():
        if sha(run / 'inputs' / name) != expected:
            raise ValueError('changed frozen input: ' + name)
    corpus = json.loads((run / 'inputs/corpus.json').read_text())
    ids = {p['package_id'] for p in corpus}
    with (run / 'inputs/source.csv').open(newline='') as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        dates = risk_dates(reader, ids)
    risk = {pid for pid, item in dates.items() if item['in_risk_window']}
    legacy = {p['package_id'] for p in corpus if p['winner_significant']}
    selected = set(plan['selected_package_ids'])
    result = {'schema': 'upworthy-2024-period-sensitivity-v1', 'status': 'post_hoc_sensitivity',
        'provider_calls': 0, 'correction_doi': SOURCE, 'date_rule': {
            'start_inclusive': START.isoformat(), 'end_inclusive': END.isoformat(),
            'basis': 'source created_at calendar date, no timezone conversion; any row overlap excludes whole experiment'},
        'interpretation': 'risk-window membership is not proof of an individual defect; remaining dates are not certified defect-free; frozen primary analysis preserved',
        'missing_source_risk_flags': [k for k in ['problem','randomization_imbalace_risk','randomization_imbalance_risk'] if k not in fields],
        'input_sha256': plan['input_sha256'], 'plan_sha256': sha(run / 'plan.json'),
        'populations': {label: {'n_total': len(group), 'n_in_window': len(group & risk)}
                        for label, group in [('corpus', ids), ('legacy_selected', legacy), ('new_selected', selected)]},
        'source_dates_by_package': dates, 'models': {}}
    for backend in ['gemini', 'azure']:
        report_path = derived / f'{backend}.json'
        report = json.loads(report_path.read_text())
        reviewer = derived / (backend + '-reviewer')
        provenance = json.loads((reviewer / 'provenance.json').read_text())
        if (provenance['report_sha256'] != sha(report_path) or
                provenance['plan_sha256'] != result['plan_sha256'] or
                provenance['journal_sha256'] != report['journal_sha256'] or
                sha(reviewer / 'variant-means.csv') != provenance['files_sha256']['variant-means.csv']):
            raise ValueError('incompatible derived lineage')
        with (reviewer / 'variant-means.csv').open(newline='') as stream:
            original = primary_vectors(corpus, report, csv.DictReader(stream), backend)
        filtered = {arm: {pid: scores for pid, scores in groups.items() if pid not in risk}
                    for arm, groups in original.items()}
        result['models'][backend] = {
            'primary_report_sha256': sha(report_path),
            'variant_means_sha256': sha(reviewer / 'variant-means.csv'),
            'raw_journal_sha256': report['journal_sha256'],
            'n_primary_complete': len(original['panel']),
            'excluded_window_package_ids': sorted(set(original['panel']) & risk),
            'n_retained': len(filtered['panel']),
            'panel': cv.analyze(filtered['panel']), 'baseline': cv.analyze(filtered['baseline']),
            'paired_gap': cv.paired_analysis(filtered['panel'], filtered['baseline'])}
    result['producer_sha256'] = {str(Path('scripts') / name): sha(Path(__file__).parent / name)
                                 for name in ['analyze_randomization_window.py', 'compute_validity.py']}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--derived-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, analyze(args.run_dir, args.derived_dir))


if __name__ == '__main__':
    main()
