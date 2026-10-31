"""Expose raw-linked observations, variant means and package metrics for offline review."""
import argparse
import base64
from collections import defaultdict
import csv
import json
from pathlib import Path

from analysis_io import new_output, write_json
from analyze_recollection import replay
import compute_validity as cv
from recollect import digest, interpret


def export(run, backend, report_path, output):
    run, output = Path(run), Path(output)
    if output.exists():
        raise FileExistsError(output)
    expected = json.loads(Path(report_path).read_text())
    checked = replay(run, backend)
    if checked != expected or checked['unresolved_observations']:
        raise ValueError('report does not describe a completed replay of these raw bytes')
    snapshot = run / checked['journal_snapshot']
    raw = snapshot.read_bytes()
    if digest(raw) != checked['journal_sha256']:
        raise ValueError('changed retained snapshot')
    tasks = json.loads((run / 'tasks.json').read_text())
    requests = {r['task_id']: r for r in json.loads((run / f'requests-{backend}.json').read_text())}
    outcomes, pending = {}, {}
    for line in raw.splitlines():
        row = json.loads(line)
        if row['event'] == 'dispatch':
            pending[row['attempt_id']] = row
        elif row['event'] == 'result':
            pending.pop(row['attempt_id'])
            if not row['terminal']:
                continue
            request = requests[row['task_id']]
            parsed = interpret(backend, base64.b64decode(row['response_body_base64']),
                               len(request['observations'])) if row['http_status'] == 200 else None
            scores = parsed['scores'] if parsed else [None] * len(request['observations'])
            for index, (observation, score) in enumerate(zip(request['observations'], scores)):
                outcomes[observation['task_id']] = {
                    'score': score, 'request_id': request['task_id'], 'choice_index': index,
                    'attempt_id': row['attempt_id'], 'response_sha256': row['response_sha256'],
                    'http_status': row['http_status'],
                    'parse_status': parsed['status'] if parsed else row['parsed']['status']}
    for attempt_id, row in pending.items():
        for index, observation in enumerate(requests[row['task_id']]['observations']):
            outcomes.setdefault(observation['task_id'], {
                'score': None, 'request_id': row['task_id'], 'choice_index': index,
                'attempt_id': attempt_id, 'response_sha256': '', 'http_status': '',
                'parse_status': 'interrupted_unknown'})
    if len(outcomes) != len(tasks):
        raise ValueError('observation export lost terminal outcomes')
    output.mkdir(parents=True)
    grouped = defaultdict(list)
    observation_fields = ['backend', 'task_id', 'package_id', 'variant_id', 'arm', 'persona_id',
                          'request_id', 'choice_index', 'attempt_id', 'score',
                          'response_sha256', 'http_status', 'parse_status']
    with new_output(output / 'observations.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=observation_fields)
        writer.writeheader()
        for task in tasks:
            arm = 'baseline' if task['persona_id'] == 'baseline' else 'panel'
            result = outcomes[task['task_id']]
            writer.writerow({**{k: task[k] for k in ['task_id', 'package_id', 'variant_id', 'persona_id']},
                             'backend': backend, 'arm': arm, **result})
            grouped[task['package_id'], task['variant_id'], arm].append(result['score'])
    corpus = json.loads((run / 'inputs/corpus.json').read_text())
    selected = set(json.loads((run / 'plan.json').read_text())['selected_package_ids'])
    complete = set(checked['primary']['panel']['package_ids'])
    package_rows = []
    fields = ['backend', 'package_id', 'variant_id', 'arm', 'real_ctr', 'planned_n', 'valid_n',
              'missing_n', 'mean', 'included_primary']
    with new_output(output / 'variant-means.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for package in corpus:
            pid = package['package_id']
            if pid not in selected:
                continue
            metrics = {}
            for arm in ['panel', 'baseline']:
                real, pred = [], []
                for variant in package['variants']:
                    values = grouped[pid, variant['variant_id'], arm]
                    valid = [v for v in values if v is not None]
                    mean = sum(valid) / len(valid) if valid else None
                    writer.writerow({'backend': backend, 'package_id': pid, 'variant_id': variant['variant_id'],
                        'arm': arm, 'real_ctr': variant['real_ctr'], 'planned_n': len(values),
                        'valid_n': len(valid), 'missing_n': len(values) - len(valid),
                        'mean': mean, 'included_primary': int(pid in complete)})
                    real.append(variant['real_ctr'])
                    pred.append(mean)
                if all(p is not None for p in pred):
                    metrics[arm] = cv.metric_values(real, pred)
                    package_rows.append({'backend': backend, 'package_id': pid, 'arm': arm,
                        'included_primary': int(pid in complete), **metrics[arm]})
            if set(metrics) == {'panel', 'baseline'}:
                gap = {key: metrics['baseline'][key] - metrics['panel'][key]
                       if metrics['baseline'][key] is not None and metrics['panel'][key] is not None
                       else None for key in cv.METRICS}
                package_rows.append({'backend': backend, 'package_id': pid, 'arm': 'baseline_minus_panel',
                    'included_primary': int(pid in complete), **gap})
    with new_output(output / 'package-metrics.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['backend', 'package_id', 'arm', 'included_primary', *cv.METRICS])
        writer.writeheader()
        writer.writerows(package_rows)
    write_json(output / 'provenance.json', {
        'backend': backend, 'plan_sha256': checked['plan_sha256'],
        'journal_sha256': checked['journal_sha256'],
        'report_sha256': digest(Path(report_path).read_bytes()),
        'files_sha256': {p.name: digest(p.read_bytes()) for p in sorted(output.glob('*.csv'))},
        'observation_rows': len(tasks), 'policy': 'blank score or metric is missing/undefined, never zero',
        'scope': 'all observations; primary flag identifies complete packages; other rows are sensitivity only'})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--backend', choices=['gemini', 'azure'], required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    export(args.run_dir, args.backend, args.report, args.output_dir)


if __name__ == '__main__':
    main()
