# beta2alpha — Full Fractal / Liquidity Validation (Option A)
_15m exec nested in 1H OBs · IRL→ERL · Dukascopy 2021-06-21→2026-06-19 (1823d) · 10-fold WF · realistic costs · 0.5% risk_

OB events nested inside a 1H OB: **38%**

| setup | session | target | trades | win% | PF | net$ | /mo@0.5% | folds+ | worst_fold | robust |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline (bias+PD) | all | erl | 1372 | 48.8 | 1.21 | 4402 | 72 | 8/10 | -516 | True |
| baseline (bias+PD) | all | fix2 | 1255 | 44.3 | 1.22 | 4444 | 73 | 8/10 | -852 | True |
| baseline (bias+PD) | london+ny | erl | 941 | 45.6 | 1.05 | 699 | 12 | 5/10 | -467 | False |
| baseline (bias+PD) | london+ny | fix2 | 906 | 40.6 | 1.05 | 817 | 13 | 6/10 | -373 | False |
| +nest | all | erl | 899 | 55.5 | 1.61 | 7099 | 117 | 9/10 | -71 | True |
| +nest | all | fix2 | 839 | 49.8 | 1.55 | 6740 | 111 | 9/10 | -10 | True |
| +nest | london+ny | erl | 558 | 53.2 | 1.42 | 3232 | 53 | 9/10 | -95 | True |
| +nest | london+ny | fix2 | 543 | 47.5 | 1.4 | 3361 | 55 | 10/10 | 80 | True |
| +irl | all | erl | 948 | 47.5 | 1.13 | 1962 | 32 | 5/10 | -485 | False |
| +irl | all | fix2 | 900 | 42.6 | 1.14 | 2169 | 36 | 6/10 | -405 | False |
| +irl | london+ny | erl | 608 | 45.2 | 1.03 | 317 | 5 | 5/10 | -517 | False |
| +irl | london+ny | fix2 | 592 | 40.0 | 1.04 | 401 | 7 | 5/10 | -612 | False |
| +nest+irl (FULL fractal) | all | erl | 600 | 52.2 | 1.41 | 3407 | 56 | 8/10 | -187 | True |
| +nest+irl (FULL fractal) | all | fix2 | 576 | 47.4 | 1.42 | 3668 | 60 | 9/10 | -248 | True |
| +nest+irl (FULL fractal) | london+ny | erl | 359 | 50.7 | 1.31 | 1588 | 26 | 8/10 | -103 | True |
| +nest+irl (FULL fractal) | london+ny | fix2 | 354 | 46.6 | 1.38 | 2069 | 34 | 8/10 | -207 | True |
