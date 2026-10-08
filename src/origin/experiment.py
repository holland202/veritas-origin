import hashlib
import json
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'evidence'

def run(seed=42, trials=100):
    rng = random.Random(seed)
    arms = {'low': 0.2, 'medium': 0.5, 'high': 0.8}
    records = []

    for strategy in ('fixed', 'random', 'adaptive'):
        counts = {k: 0 for k in arms}
        rewards = {k: 0 for k in arms}

        for step in range(trials):
            if strategy == 'fixed':
                arm = 'medium'
            elif strategy == 'random':
                arm = rng.choice(list(arms))
            else:
                unexplored = [
                    k for k in arms if counts[k] == 0
                ]
                arm = unexplored[0] if unexplored else max(
                    arms,
                    key=lambda k:
                    rewards[k] / counts[k]
                    + (
                        2 * __import__('math').log(step + 1)
                        / counts[k]
                    ) ** 0.5
                )

            reward = int(rng.random() < arms[arm])
            counts[arm] += 1
            rewards[arm] += reward
            records.append({
                'strategy': strategy,
                'step': step,
                'arm': arm,
                'reward': reward
            })

    return {
        'seed': seed,
        'trials_per_strategy': trials,
        'environment': arms,
        'records': records
    }

def save(result):
    OUT.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        result, sort_keys=True, indent=2
    ).encode()

    digest = hashlib.sha256(payload).hexdigest()
    stamp = datetime.now(timezone.utc).strftime(
        '%Y%m%dT%H%M%S%fZ'
    )
    path = OUT / (
        f'pilot-{stamp}-{uuid.uuid4().hex[:8]}.json'
    )

    with path.open('xb') as f:
        f.write(payload)

    return path, digest

if __name__ == '__main__':
    result = run()
    path, digest = save(result)

    print('Evidence:', path)
    print('SHA256:', digest)

    for strategy in ('fixed', 'random', 'adaptive'):
        rows = [
            r for r in result['records']
            if r['strategy'] == strategy
        ]
        print(
            strategy,
            sum(r['reward'] for r in rows),
            '/', len(rows)
        )

    print('STATUS: EXPLORATORY — NOT VALIDATED')
