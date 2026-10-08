import hashlib
import json
import math
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARMS = {'low': 0.2, 'medium': 0.5, 'high': 0.8}
POLICIES = ('fixed-medium', 'random', 'ucb1')
TRIALS = 100
SEEDS = range(100)

def potential_outcomes(seed):
    return {
        arm: [
            int(
                random.Random(f'{seed}:{arm}:{i}').random() < p
            )
            for i in range(TRIALS)
        ]
        for arm, p in ARMS.items()
    }

def evaluate(seed, policy, outcomes):
    counts = {arm: 0 for arm in ARMS}
    rewards = {arm: 0 for arm in ARMS}
    chooser = random.Random(f'choice:{seed}')
    records = []

    for step in range(TRIALS):
        if policy == 'fixed-medium':
            arm = 'medium'
        elif policy == 'random':
            arm = chooser.choice(tuple(ARMS))
        else:
            unexplored = [
                arm for arm in ARMS if counts[arm] == 0
            ]
            arm = (
                unexplored[0] if unexplored else max(
                    ARMS,
                    key=lambda a:
                    rewards[a] / counts[a]
                    + math.sqrt(
                        2 * math.log(step + 1) / counts[a]
                    )
                )
            )

        reward = outcomes[arm][counts[arm]]
        counts[arm] += 1
        rewards[arm] += reward
        records.append({
            'step': step,
            'arm': arm,
            'reward': reward
        })

    return {
        'seed': seed,
        'policy': policy,
        'total_reward': sum(rewards.values()),
        'records': records
    }

def run():
    results = []

    for seed in SEEDS:
        outcomes = potential_outcomes(seed)
        for policy in POLICIES:
            results.append(
                evaluate(seed, policy, outcomes)
            )

    means = {
        policy: sum(
            r['total_reward']
            for r in results
            if r['policy'] == policy
        ) / len(SEEDS)
        for policy in POLICIES
    }

    supported = all(
        means['ucb1'] - means[baseline] >= 5
        for baseline in ('fixed-medium', 'random')
    )

    return {
        'experiment': 'EXP002',
        'status': 'CONFIRMATORY_RUN',
        'seeds': [0, 99],
        'trials_per_policy_per_seed': TRIALS,
        'arm_probabilities': ARMS,
        'means': means,
        'criterion_met': supported,
        'results': results
    }

def save(data):
    out = ROOT / 'evidence' / 'exp002'
    out.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime(
        '%Y%m%dT%H%M%S%fZ'
    )
    path = out / (
        f'exp002-{stamp}-{uuid.uuid4().hex[:8]}.json'
    )

    payload = json.dumps(
        data, sort_keys=True, indent=2
    ).encode()

    with path.open('xb') as handle:
        handle.write(payload)

    return path, hashlib.sha256(payload).hexdigest()

if __name__ == '__main__':
    data = run()
    path, digest = save(data)

    print('Evidence:', path)
    print('SHA256:', digest)
    print('Mean rewards:', data['means'])
    print(
        'Preregistered criterion met:',
        data['criterion_met']
    )
    print(
        'STATUS: CONFIRMATORY RESULT '
        '— NOT INDEPENDENTLY VALIDATED'
    )
