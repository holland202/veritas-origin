# TSP-002 assisted-cooling repeatability comparison (2026-10-11)

Research Director, Orchestrator, and Project Owner: Chad Holland.

## Evidence class
OWNER-REPORTED TERMUX EXECUTION AND SUMMARY STATISTICS. No independent access to raw device logs. Samsung S25 Ultra, Shizuku ADB shell thermalservice, Black Shark external cooling fan ON both runs; workload labeled NORMAL_IDLE. Fan speed, ambient temperature, charging state, and intervening activity not recorded. Current HAL values only; cached values excluded from analysis.

## Run provenance
- Run 1: `thermal_fan_on_20261011_082345.log`, SHA-256 owner-reported `846bb4ba55d336ff3637f4deef6eae7b1927450155374c72d3c14c08104111ab`. 11 samples, timestamps 08:23:45 to 08:28:52 -05:00; all `RISH_EXIT_CODE=0`, thermal status 0 in all 11 samples.
- Run 2: `thermal_fan_on_repeat_20261011_083640.log`, SHA-256 owner-reported `45bb17a5afa5758f39e46a1a8eca121966d34df65cf58de392fd1445b7b82859`. 11 samples, timestamps 08:36:40 to 08:41:45 -05:00; all `RISH_EXIT_CODE=0`. Final `END` recorded 08:44:55, after sampling. Run 2 thermal statuses not yet separately displayed in transcript.

## Owner-computed current HAL statistics (°C)

| Sensor | Run 1 n/min/mean/max | Run 2 n/min/mean/max | Mean delta R2-R1 |
| --- | --- | --- | --- |
| AP | 11 / 26.0 / 27.85 / 32.2 | 11 / 24.4 / 26.48 / 29.5 | -1.37 |
| BAT | 11 / 26.5 / 27.07 / 27.5 | 11 / 19.2 / 22.28 / 26.4 | -4.79 |
| PA | 11 / 26.5 / 28.35 / 32.5 | 11 / 24.8 / 26.97 / 29.7 | -1.38 |
| SKIN | 11 / 27.6 / 28.40 / 29.3 | 11 / 25.9 / 27.36 / 28.5 | -1.04 |

## Interpretation
Successful owner-reported repeated collection; thermal baseline *stationarity/repeatability not established*. Battery mean differs by 4.79°C and run 2 BAT range is 7.2°C. No causal inference of cooling effect. These are temperatures with external cooling assistance, not uncooled device baseline. Cached HAL values must not be conflated with current HAL. Raw logs should remain unchanged. Independent validation and fan-on/off comparisons are pending.
