# beta2alpha — Walk-Forward Strategy Sweep

_2 years Dukascopy XAU/USD · realistic costs (spread 0.45, slippage 0.1/side, commission $7.0/lot, min-stop $2.0) · 6-fold walk-forward · 0.5% risk ($25)/trade_

**Tested 675 configurations. ROBUST (profitable in ≥5/6 folds, net>0, ≥40 trades): 118.**


**Folds:** F1:2024-06-20→2024-10-20 | F2:2024-10-20→2025-02-18 | F3:2025-02-18→2025-06-20 | F4:2025-06-20→2025-10-19 | F5:2025-10-19→2026-02-18 | F6:2026-02-18→2026-06-19


## 1. ROBUST configurations (survive walk-forward)

| tf | session | setup | filters | target | trades | win% | PF | net$ | /mo@0.5% | folds+ | worst_fold$ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5m | all | ob | bias | fix2 | 2034 | 47.4 | 1.42 | 12870 | 536 | 6/6 | 998 |
| 5m | all | fvg | bias | fix2 | 2981 | 46.0 | 1.22 | 10992 | 458 | 5/6 | -461 |
| 5m | all | ob | bias | fix3 | 2340 | 51.6 | 1.29 | 9264 | 386 | 6/6 | 274 |
| 5m | all | ob | bias | struct | 2340 | 51.6 | 1.29 | 9264 | 386 | 6/6 | 274 |
| 15m | all | ob | bias | fix2 | 730 | 49.6 | 1.66 | 6700 | 279 | 6/6 | 789 |
| 5m | all | fvg | bias | fix3 | 3241 | 50.9 | 1.13 | 6583 | 274 | 5/6 | -979 |
| 5m | all | fvg | bias | struct | 3241 | 50.9 | 1.13 | 6583 | 274 | 5/6 | -979 |
| 5m | asian | fvg | bias | fix2 | 1138 | 48.2 | 1.35 | 6251 | 260 | 6/6 | 173 |
| 15m | all | ob | bias | fix3 | 860 | 53.7 | 1.55 | 6025 | 251 | 6/6 | 438 |
| 15m | all | ob | bias | struct | 860 | 53.7 | 1.55 | 6025 | 251 | 6/6 | 438 |
| 5m | all | ob | pd+bias | fix2 | 1531 | 43.7 | 1.22 | 5435 | 226 | 5/6 | -66 |
| 5m | london+ny | ob | bias | fix2 | 1151 | 44.9 | 1.3 | 5310 | 221 | 6/6 | 200 |
| 5m | london+ny | fvg | bias | fix2 | 1232 | 46.3 | 1.25 | 4972 | 207 | 5/6 | -695 |
| 15m | all | fvg | bias | fix2 | 1161 | 45.1 | 1.23 | 4466 | 186 | 6/6 | 319 |
| 5m | asian | fvg | bias | fix3 | 1220 | 53.0 | 1.25 | 4393 | 183 | 5/6 | -89 |
| 5m | asian | fvg | bias | struct | 1220 | 53.0 | 1.25 | 4393 | 183 | 5/6 | -89 |
| 5m | asian | ob | bias | fix2 | 1029 | 44.8 | 1.26 | 4250 | 177 | 5/6 | -244 |
| 5m | ny | ob | bias | fix2 | 760 | 45.5 | 1.33 | 3907 | 163 | 5/6 | -181 |
| 5m | london+ny | ob | bias | fix3 | 1263 | 49.9 | 1.21 | 3730 | 155 | 6/6 | 76 |
| 5m | london+ny | ob | bias | struct | 1263 | 49.9 | 1.21 | 3730 | 155 | 6/6 | 76 |
| 1h | all | fvg | bias | fix3 | 308 | 51.6 | 1.83 | 3612 | 150 | 6/6 | 162 |
| 1h | all | fvg | bias | struct | 308 | 51.6 | 1.83 | 3612 | 150 | 6/6 | 162 |
| 5m | ny | fvg | bias | fix2 | 722 | 47.1 | 1.29 | 3427 | 143 | 5/6 | -579 |
| 15m | all | ob | pd+bias | fix2 | 489 | 46.6 | 1.47 | 3396 | 142 | 6/6 | 112 |
| 15m | all | fvg | bias | fix3 | 1230 | 48.9 | 1.18 | 3345 | 139 | 6/6 | 151 |
| 15m | all | fvg | bias | struct | 1230 | 48.9 | 1.18 | 3345 | 139 | 6/6 | 151 |
| 5m | ny | fvg | raw | fix2 | 1432 | 43.4 | 1.13 | 3147 | 131 | 5/6 | -413 |
| 5m | all | ob | pd+bias | fix3 | 1655 | 48.5 | 1.12 | 3038 | 127 | 5/6 | -424 |
| 5m | all | ob | pd+bias | struct | 1655 | 48.5 | 1.12 | 3038 | 127 | 5/6 | -424 |
| 5m | all | ob | pd+bias+sweep | fix2 | 1050 | 42.8 | 1.16 | 2859 | 119 | 5/6 | -1 |
| 5m | asian | ob | bias | fix3 | 1150 | 49.9 | 1.17 | 2807 | 117 | 5/6 | -560 |
| 5m | asian | ob | bias | struct | 1150 | 49.9 | 1.17 | 2807 | 117 | 5/6 | -560 |
| 5m | ny | ob | bias | fix3 | 819 | 50.3 | 1.24 | 2796 | 117 | 5/6 | -71 |
| 5m | ny | ob | bias | struct | 819 | 50.3 | 1.24 | 2796 | 117 | 5/6 | -71 |
| 1h | all | ob | bias | fix3 | 292 | 51.7 | 1.71 | 2643 | 110 | 6/6 | 303 |
| 1h | all | ob | bias | struct | 292 | 51.7 | 1.71 | 2643 | 110 | 6/6 | 303 |
| 1h | all | ob | bias | fix2 | 267 | 48.3 | 1.7 | 2556 | 107 | 6/6 | 301 |
| 15m | all | ob | pd+bias | fix3 | 546 | 50.5 | 1.34 | 2525 | 105 | 6/6 | 13 |
| 15m | all | ob | pd+bias | struct | 546 | 50.5 | 1.34 | 2525 | 105 | 6/6 | 13 |
| 15m | london+ny | ob | bias | fix2 | 584 | 42.6 | 1.27 | 2446 | 102 | 6/6 | 120 |
| 5m | ny | fvg | bias | fix3 | 744 | 52.2 | 1.21 | 2275 | 95 | 5/6 | -554 |
| 5m | ny | fvg | bias | struct | 744 | 52.2 | 1.21 | 2275 | 95 | 5/6 | -554 |
| 5m | london+ny | ob | pd+bias | fix2 | 763 | 42.6 | 1.18 | 2200 | 92 | 5/6 | -47 |
| 1h | all | fvg | bias | fix2 | 297 | 48.8 | 1.5 | 2193 | 91 | 6/6 | 55 |
| 15m | london+ny | ob | bias | fix3 | 630 | 48.1 | 1.24 | 2187 | 91 | 6/6 | 220 |
| 15m | london+ny | ob | bias | struct | 630 | 48.1 | 1.24 | 2187 | 91 | 6/6 | 220 |
| 15m | asian | fvg | bias | fix2 | 552 | 45.1 | 1.23 | 2125 | 89 | 5/6 | -254 |
| 1h | london+ny | fvg | bias | fix3 | 164 | 51.8 | 1.87 | 1980 | 82 | 6/6 | 82 |
| 1h | london+ny | fvg | bias | struct | 164 | 51.8 | 1.87 | 1980 | 82 | 6/6 | 82 |
| 15m | all | fvg | pd+bias | fix2 | 604 | 44.4 | 1.18 | 1866 | 78 | 5/6 | -120 |
| 5m | london+ny | fvg | pd+bias | fix2 | 635 | 44.9 | 1.17 | 1826 | 76 | 5/6 | -355 |
| 5m | london | ob | bias | fix2 | 604 | 43.0 | 1.18 | 1792 | 75 | 5/6 | -167 |
| 5m | all | fvg | pd+bias+sweep | fix2 | 840 | 43.7 | 1.12 | 1728 | 72 | 5/6 | -511 |
| 15m | all | ob | pd+bias+mss | fix2 | 306 | 44.8 | 1.35 | 1643 | 68 | 5/6 | -36 |
| 5m | asian | fvg | pd+bias | fix2 | 533 | 45.0 | 1.17 | 1543 | 64 | 5/6 | -805 |
| 5m | london+ny | fvg | pd+bias+sweep | fix2 | 322 | 46.9 | 1.28 | 1467 | 61 | 5/6 | -73 |
| 5m | london+ny | ob | pd+bias | fix3 | 792 | 48.4 | 1.12 | 1404 | 59 | 5/6 | -14 |
| 5m | london+ny | ob | pd+bias | struct | 792 | 48.4 | 1.12 | 1404 | 59 | 5/6 | -14 |
| 15m | ny | ob | bias | fix2 | 432 | 41.0 | 1.19 | 1331 | 55 | 5/6 | -16 |
| 15m | all | ob | pd+bias+mss | fix3 | 316 | 49.4 | 1.29 | 1284 | 53 | 6/6 | 53 |
| 15m | all | ob | pd+bias+mss | struct | 316 | 49.4 | 1.29 | 1284 | 53 | 6/6 | 53 |
| 5m | ny | fvg | pd+bias+sweep | fix2 | 183 | 49.7 | 1.45 | 1255 | 52 | 5/6 | -57 |
| 15m | all | ob | pd+bias+sweep | fix2 | 355 | 41.7 | 1.22 | 1240 | 52 | 5/6 | -246 |
| 1h | ny | ob | bias | fix2 | 150 | 46.7 | 1.57 | 1219 | 51 | 6/6 | 75 |
| 1h | london+ny | fvg | bias | fix2 | 163 | 48.5 | 1.5 | 1208 | 50 | 6/6 | 54 |
| 1h | london | fvg | bias | fix3 | 97 | 51.5 | 1.86 | 1168 | 49 | 6/6 | 35 |
| 1h | london | fvg | bias | struct | 97 | 51.5 | 1.86 | 1168 | 49 | 6/6 | 35 |
| 1h | all | ob | raw | fix3 | 277 | 44.4 | 1.28 | 1142 | 48 | 5/6 | -287 |
| 1h | all | ob | raw | struct | 277 | 44.4 | 1.28 | 1142 | 48 | 5/6 | -287 |
| 1h | ny | fvg | bias | fix3 | 95 | 51.6 | 1.84 | 1122 | 47 | 5/6 | -67 |
| 1h | ny | fvg | bias | struct | 95 | 51.6 | 1.84 | 1122 | 47 | 5/6 | -67 |
| 1h | asian | fvg | bias | fix3 | 202 | 45.0 | 1.34 | 1100 | 46 | 5/6 | -216 |
| 1h | asian | fvg | bias | struct | 202 | 45.0 | 1.34 | 1100 | 46 | 5/6 | -216 |
| 5m | ny | fvg | pd+bias | fix2 | 363 | 44.9 | 1.18 | 1085 | 45 | 5/6 | -317 |
| 1h | ny | ob | bias | fix3 | 152 | 48.0 | 1.51 | 1076 | 45 | 6/6 | 54 |
| 1h | ny | ob | bias | struct | 152 | 48.0 | 1.51 | 1076 | 45 | 6/6 | 54 |
| 5m | all | ob | pd+bias+sweep | fix3 | 1101 | 47.5 | 1.06 | 1069 | 45 | 5/6 | -84 |
| 5m | all | ob | pd+bias+sweep | struct | 1101 | 47.5 | 1.06 | 1069 | 45 | 5/6 | -84 |
| 15m | ny | ob | bias | fix3 | 452 | 46.0 | 1.16 | 1046 | 44 | 6/6 | 52 |
| 15m | ny | ob | bias | struct | 452 | 46.0 | 1.16 | 1046 | 44 | 6/6 | 52 |
| 5m | london+ny | fvg | pd+bias | fix3 | 641 | 50.4 | 1.11 | 1039 | 43 | 5/6 | -271 |
| 5m | london+ny | fvg | pd+bias | struct | 641 | 50.4 | 1.11 | 1039 | 43 | 5/6 | -271 |
| 5m | asian | fvg | pd+bias | fix3 | 551 | 50.8 | 1.12 | 1005 | 42 | 5/6 | -827 |
| 5m | asian | fvg | pd+bias | struct | 551 | 50.8 | 1.12 | 1005 | 42 | 5/6 | -827 |
| 1h | all | ob | pd+bias | fix2 | 142 | 45.1 | 1.48 | 988 | 41 | 6/6 | 60 |
| 5m | ny | ob | pd+bias+sweep | fix2 | 288 | 43.1 | 1.21 | 966 | 40 | 5/6 | -487 |
| 15m | all | fvg | pd+bias+sweep | fix2 | 300 | 44.0 | 1.19 | 937 | 39 | 5/6 | -285 |
| 1h | all | ob | pd+bias | fix3 | 143 | 47.6 | 1.46 | 913 | 38 | 6/6 | 29 |
| 1h | all | ob | pd+bias | struct | 143 | 47.6 | 1.46 | 913 | 38 | 6/6 | 29 |
| 15m | ny | ob | pd+bias+mss | fix2 | 109 | 47.7 | 1.54 | 859 | 36 | 6/6 | 9 |
| 5m | london+ny | fvg | pd+bias+sweep | fix3 | 324 | 51.5 | 1.17 | 812 | 34 | 5/6 | -43 |
| 5m | london+ny | fvg | pd+bias+sweep | struct | 324 | 51.5 | 1.17 | 812 | 34 | 5/6 | -43 |
| 1h | london+ny | fvg | pd+bias | fix3 | 68 | 48.5 | 1.78 | 781 | 33 | 5/6 | -165 |
| 1h | london+ny | fvg | pd+bias | struct | 68 | 48.5 | 1.78 | 781 | 33 | 5/6 | -165 |
| 15m | london+ny | ob | pd+bias | fix2 | 353 | 40.2 | 1.13 | 771 | 32 | 5/6 | -309 |
| 1h | london+ny | ob | bias | fix3 | 206 | 43.2 | 1.24 | 767 | 32 | 5/6 | -3 |
| 1h | london+ny | ob | bias | struct | 206 | 43.2 | 1.24 | 767 | 32 | 5/6 | -3 |
| 15m | all | ob | pd+bias+sweep+mss | fix2 | 132 | 44.7 | 1.36 | 731 | 30 | 5/6 | -137 |
| 15m | london+ny | ob | pd+bias+mss | fix2 | 153 | 43.8 | 1.3 | 729 | 30 | 5/6 | -92 |
| 5m | ny | fvg | pd+bias+sweep | fix3 | 185 | 53.5 | 1.27 | 704 | 29 | 5/6 | -25 |
| 5m | ny | fvg | pd+bias+sweep | struct | 185 | 53.5 | 1.27 | 704 | 29 | 5/6 | -25 |
| 15m | ny | ob | pd+bias+mss | fix3 | 110 | 52.7 | 1.47 | 676 | 28 | 5/6 | -52 |
| 15m | ny | ob | pd+bias+mss | struct | 110 | 52.7 | 1.47 | 676 | 28 | 5/6 | -52 |
| 1h | london+ny | ob | bias | fix2 | 199 | 39.7 | 1.19 | 598 | 25 | 5/6 | -10 |
| 1h | london | fvg | bias | fix2 | 97 | 46.4 | 1.39 | 587 | 24 | 5/6 | -130 |
| 1h | ny | ob | pd+bias | fix2 | 68 | 47.1 | 1.57 | 556 | 23 | 6/6 | 16 |
| 15m | all | fvg | pd+bias+sweep | fix3 | 309 | 47.9 | 1.11 | 538 | 22 | 5/6 | -337 |
| 15m | all | fvg | pd+bias+sweep | struct | 309 | 47.9 | 1.11 | 538 | 22 | 5/6 | -337 |
| 1h | all | fvg | pd+bias+sweep | fix3 | 67 | 47.8 | 1.53 | 534 | 22 | 6/6 | 28 |
| 1h | all | fvg | pd+bias+sweep | struct | 67 | 47.8 | 1.53 | 534 | 22 | 6/6 | 28 |
| 1h | all | ob | raw | fix2 | 265 | 38.5 | 1.11 | 480 | 20 | 5/6 | -245 |
| 15m | london+ny | fvg | pd+bias+sweep | fix2 | 138 | 44.2 | 1.21 | 475 | 20 | 5/6 | -233 |
| 15m | ny | fvg | pd+bias+sweep | fix2 | 82 | 46.3 | 1.33 | 426 | 18 | 5/6 | -26 |
| 5m | london | fvg | pd+bias+sweep | fix2 | 147 | 44.9 | 1.16 | 411 | 17 | 5/6 | -238 |
| 1h | london+ny | fvg | raw | fix2 | 318 | 39.6 | 1.05 | 266 | 11 | 5/6 | -391 |
| 1h | london | ob | pd+sweep | fix3 | 52 | 46.2 | 1.23 | 169 | 7 | 5/6 | -28 |
| 1h | london | ob | pd+sweep | struct | 52 | 46.2 | 1.23 | 169 | 7 | 5/6 | -28 |
| 1h | asian | sweep | bias | fix2 | 98 | 38.8 | 1.1 | 157 | 7 | 5/6 | -80 |


## 2. Per-fold net ($) for robust configs

| tf | session | setup | filters | target | F1 | F2 | F3 | F4 | F5 | F6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5m | all | ob | bias | fix2 | 1896 | 998 | 1782 | 2523 | 2654 | 3018 |
| 5m | all | fvg | bias | fix2 | 506 | -461 | 1651 | 1286 | 3062 | 4979 |
| 5m | all | ob | bias | fix3 | 1271 | 274 | 1071 | 1935 | 2063 | 2650 |
| 5m | all | ob | bias | struct | 1271 | 274 | 1071 | 1935 | 2063 | 2650 |
| 15m | all | ob | bias | fix2 | 1158 | 997 | 1258 | 1036 | 1463 | 789 |
| 5m | all | fvg | bias | fix3 | 367 | -979 | 960 | 281 | 2163 | 3823 |
| 5m | all | fvg | bias | struct | 367 | -979 | 960 | 281 | 2163 | 3823 |
| 5m | asian | fvg | bias | fix2 | 267 | 173 | 585 | 833 | 1760 | 2633 |
| 15m | all | ob | bias | fix3 | 1209 | 654 | 976 | 1090 | 1657 | 438 |
| 15m | all | ob | bias | struct | 1209 | 654 | 976 | 1090 | 1657 | 438 |
| 5m | all | ob | pd+bias | fix2 | 533 | -66 | 1073 | 1142 | 1381 | 1371 |
| 5m | london+ny | ob | bias | fix2 | 997 | 611 | 845 | 1786 | 200 | 871 |
| 5m | london+ny | fvg | bias | fix2 | 110 | -695 | 809 | 1433 | 1687 | 1629 |
| 15m | all | fvg | bias | fix2 | 319 | 816 | 371 | 727 | 1427 | 806 |
| 5m | asian | fvg | bias | fix3 | 200 | -89 | 401 | 614 | 1604 | 1662 |
| 5m | asian | fvg | bias | struct | 200 | -89 | 401 | 614 | 1604 | 1662 |
| 5m | asian | ob | bias | fix2 | 541 | -244 | 548 | 460 | 1324 | 1622 |
| 5m | ny | ob | bias | fix2 | -181 | 421 | 1123 | 1646 | 318 | 580 |
| 5m | london+ny | ob | bias | fix3 | 741 | 544 | 108 | 1480 | 76 | 781 |
| 5m | london+ny | ob | bias | struct | 741 | 544 | 108 | 1480 | 76 | 781 |
| 1h | all | fvg | bias | fix3 | 1239 | 854 | 388 | 406 | 562 | 162 |
| 1h | all | fvg | bias | struct | 1239 | 854 | 388 | 406 | 562 | 162 |
| 5m | ny | fvg | bias | fix2 | 193 | -579 | 540 | 1309 | 908 | 1055 |
| 15m | all | ob | pd+bias | fix2 | 742 | 528 | 702 | 112 | 1057 | 255 |
| 15m | all | fvg | bias | fix3 | 151 | 440 | 519 | 680 | 1288 | 266 |
| 15m | all | fvg | bias | struct | 151 | 440 | 519 | 680 | 1288 | 266 |
| 5m | ny | fvg | raw | fix2 | 580 | -413 | 786 | 387 | 1107 | 700 |
| 5m | all | ob | pd+bias | fix3 | 261 | -424 | 498 | 688 | 1029 | 985 |
| 5m | all | ob | pd+bias | struct | 261 | -424 | 498 | 688 | 1029 | 985 |
| 5m | all | ob | pd+bias+sweep | fix2 | 261 | -1 | 97 | 713 | 961 | 827 |
| 5m | asian | ob | bias | fix3 | 373 | -560 | 547 | 93 | 896 | 1458 |
| 5m | asian | ob | bias | struct | 373 | -560 | 547 | 93 | 896 | 1458 |
| 5m | ny | ob | bias | fix3 | -71 | 282 | 609 | 1246 | 195 | 536 |
| 5m | ny | ob | bias | struct | -71 | 282 | 609 | 1246 | 195 | 536 |
| 1h | all | ob | bias | fix3 | 440 | 377 | 485 | 642 | 303 | 395 |
| 1h | all | ob | bias | struct | 440 | 377 | 485 | 642 | 303 | 395 |
| 1h | all | ob | bias | fix2 | 335 | 539 | 301 | 514 | 404 | 463 |
| 15m | all | ob | pd+bias | fix3 | 595 | 167 | 476 | 13 | 1207 | 67 |
| 15m | all | ob | pd+bias | struct | 595 | 167 | 476 | 13 | 1207 | 67 |
| 15m | london+ny | ob | bias | fix2 | 120 | 450 | 529 | 484 | 460 | 404 |
| 5m | ny | fvg | bias | fix3 | 117 | -554 | 77 | 1164 | 600 | 870 |
| 5m | ny | fvg | bias | struct | 117 | -554 | 77 | 1164 | 600 | 870 |
| 5m | london+ny | ob | pd+bias | fix2 | 344 | -47 | 699 | 1008 | 103 | 92 |
| 1h | all | fvg | bias | fix2 | 1072 | 401 | 157 | 55 | 397 | 111 |
| 15m | london+ny | ob | bias | fix3 | 220 | 272 | 441 | 539 | 411 | 304 |
| 15m | london+ny | ob | bias | struct | 220 | 272 | 441 | 539 | 411 | 304 |
| 15m | asian | fvg | bias | fix2 | -254 | 606 | 128 | 889 | 627 | 129 |
| 1h | london+ny | fvg | bias | fix3 | 342 | 391 | 658 | 281 | 227 | 82 |
| 1h | london+ny | fvg | bias | struct | 342 | 391 | 658 | 281 | 227 | 82 |
| 15m | all | fvg | pd+bias | fix2 | 139 | 514 | 356 | -120 | 772 | 206 |
| 5m | london+ny | fvg | pd+bias | fix2 | 83 | -355 | 492 | 205 | 638 | 763 |
| 5m | london | ob | bias | fix2 | 1223 | 256 | 25 | 261 | -167 | 194 |
| 5m | all | fvg | pd+bias+sweep | fix2 | 138 | -511 | 121 | 9 | 1287 | 683 |
| 15m | all | ob | pd+bias+mss | fix2 | 208 | 46 | -36 | 482 | 720 | 224 |
| 5m | asian | fvg | pd+bias | fix2 | 119 | 172 | 351 | -805 | 498 | 1209 |
| 5m | london+ny | fvg | pd+bias+sweep | fix2 | 89 | -73 | 127 | 434 | 388 | 501 |
| 5m | london+ny | ob | pd+bias | fix3 | 359 | 54 | 254 | 688 | 63 | -14 |
| 5m | london+ny | ob | pd+bias | struct | 359 | 54 | 254 | 688 | 63 | -14 |
| 15m | ny | ob | bias | fix2 | 42 | 282 | -16 | 263 | 280 | 481 |
| 15m | all | ob | pd+bias+mss | fix3 | 119 | 73 | 53 | 322 | 622 | 94 |
| 15m | all | ob | pd+bias+mss | struct | 119 | 73 | 53 | 322 | 622 | 94 |
| 5m | ny | fvg | pd+bias+sweep | fix2 | -57 | 208 | 187 | 272 | 301 | 344 |
| 15m | all | ob | pd+bias+sweep | fix2 | 401 | 274 | 65 | -246 | 439 | 307 |
| 1h | ny | ob | bias | fix2 | 75 | 217 | 185 | 320 | 220 | 202 |
| 1h | london+ny | fvg | bias | fix2 | 305 | 54 | 490 | 88 | 187 | 84 |
| 1h | london | fvg | bias | fix3 | 35 | 89 | 231 | 365 | 226 | 221 |
| 1h | london | fvg | bias | struct | 35 | 89 | 231 | 365 | 226 | 221 |
| 1h | all | ob | raw | fix3 | 273 | 123 | 422 | 516 | 95 | -287 |
| 1h | all | ob | raw | struct | 273 | 123 | 422 | 516 | 95 | -287 |
| 1h | ny | fvg | bias | fix3 | 308 | 260 | 452 | -67 | 134 | 36 |
| 1h | ny | fvg | bias | struct | 308 | 260 | 452 | -67 | 134 | 36 |
| 1h | asian | fvg | bias | fix3 | 414 | 131 | -216 | 201 | 563 | 7 |
| 1h | asian | fvg | bias | struct | 414 | 131 | -216 | 201 | 563 | 7 |
| 5m | ny | fvg | pd+bias | fix2 | 128 | -317 | 236 | 175 | 299 | 564 |
| 1h | ny | ob | bias | fix3 | 54 | 177 | 372 | 239 | 123 | 111 |
| 1h | ny | ob | bias | struct | 54 | 177 | 372 | 239 | 123 | 111 |
| 5m | all | ob | pd+bias+sweep | fix3 | 97 | -84 | 44 | 26 | 460 | 526 |
| 5m | all | ob | pd+bias+sweep | struct | 97 | -84 | 44 | 26 | 460 | 526 |
| 15m | ny | ob | bias | fix3 | 80 | 52 | 163 | 345 | 108 | 299 |
| 15m | ny | ob | bias | struct | 80 | 52 | 163 | 345 | 108 | 299 |
| 5m | london+ny | fvg | pd+bias | fix3 | 15 | -271 | 49 | 50 | 425 | 771 |
| 5m | london+ny | fvg | pd+bias | struct | 15 | -271 | 49 | 50 | 425 | 771 |
| 5m | asian | fvg | pd+bias | fix3 | 208 | 107 | 214 | -827 | 704 | 598 |
| 5m | asian | fvg | pd+bias | struct | 208 | 107 | 214 | -827 | 704 | 598 |
| 1h | all | ob | pd+bias | fix2 | 60 | 209 | 225 | 189 | 123 | 182 |
| 5m | ny | ob | pd+bias+sweep | fix2 | 16 | -487 | 533 | 705 | 145 | 54 |
| 15m | all | fvg | pd+bias+sweep | fix2 | 232 | 150 | 226 | -285 | 147 | 466 |
| 1h | all | ob | pd+bias | fix3 | 29 | 162 | 420 | 126 | 55 | 120 |
| 1h | all | ob | pd+bias | struct | 29 | 162 | 420 | 126 | 55 | 120 |
| 15m | ny | ob | pd+bias+mss | fix2 | 186 | 17 | 9 | 209 | 236 | 200 |
| 5m | london+ny | fvg | pd+bias+sweep | fix3 | 103 | -43 | 40 | 115 | 237 | 361 |
| 5m | london+ny | fvg | pd+bias+sweep | struct | 103 | -43 | 40 | 115 | 237 | 361 |
| 1h | london+ny | fvg | pd+bias | fix3 | 176 | 111 | 441 | 98 | 120 | -165 |
| 1h | london+ny | fvg | pd+bias | struct | 176 | 111 | 441 | 98 | 120 | -165 |
| 15m | london+ny | ob | pd+bias | fix2 | 90 | 11 | 405 | -309 | 404 | 171 |
| 1h | london+ny | ob | bias | fix3 | 52 | 88 | 427 | 170 | 34 | -3 |
| 1h | london+ny | ob | bias | struct | 52 | 88 | 427 | 170 | 34 | -3 |
| 15m | all | ob | pd+bias+sweep+mss | fix2 | 143 | 191 | -137 | 51 | 209 | 275 |
| 15m | london+ny | ob | pd+bias+mss | fix2 | 80 | -92 | 63 | 307 | 229 | 142 |
| 5m | ny | fvg | pd+bias+sweep | fix3 | -25 | 186 | 74 | 126 | 81 | 261 |
| 5m | ny | fvg | pd+bias+sweep | struct | -25 | 186 | 74 | 126 | 81 | 261 |
| 15m | ny | ob | pd+bias+mss | fix3 | 57 | -52 | 139 | 146 | 223 | 163 |
| 15m | ny | ob | pd+bias+mss | struct | 57 | -52 | 139 | 146 | 223 | 163 |
| 1h | london+ny | ob | bias | fix2 | 10 | -10 | 173 | 193 | 137 | 95 |
| 1h | london | fvg | bias | fix2 | 26 | -130 | 151 | 261 | 133 | 145 |
| 1h | ny | ob | pd+bias | fix2 | 45 | 84 | 199 | 99 | 16 | 114 |
| 15m | all | fvg | pd+bias+sweep | fix3 | 81 | 147 | 272 | -337 | 81 | 295 |
| 15m | all | fvg | pd+bias+sweep | struct | 81 | 147 | 272 | -337 | 81 | 295 |
| 1h | all | fvg | pd+bias+sweep | fix3 | 249 | 32 | 28 | 39 | 126 | 61 |
| 1h | all | fvg | pd+bias+sweep | struct | 249 | 32 | 28 | 39 | 126 | 61 |
| 1h | all | ob | raw | fix2 | 35 | 55 | 289 | 233 | 115 | -245 |
| 15m | london+ny | fvg | pd+bias+sweep | fix2 | 183 | 80 | 355 | -233 | 12 | 77 |
| 15m | ny | fvg | pd+bias+sweep | fix2 | 157 | 52 | 219 | 5 | 18 | -26 |
| 5m | london | fvg | pd+bias+sweep | fix2 | 156 | -238 | 25 | 133 | 133 | 202 |
| 1h | london+ny | fvg | raw | fix2 | 130 | 11 | 486 | -391 | 19 | 10 |
| 1h | london | ob | pd+sweep | fix3 | 24 | -28 | 3 | 66 | 82 | 22 |
| 1h | london | ob | pd+sweep | struct | 24 | -28 | 3 | 66 | 82 | 22 |
| 1h | asian | sweep | bias | fix2 | 108 | 18 | 69 | 36 | -80 | 6 |


## 3. Top 25 by total net (robust or not — for context)

| tf | session | setup | filters | target | trades | win% | PF | net$ | /mo@0.5% | folds+ | worst_fold$ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5m | all | ob | bias | fix2 | 2034 | 47.4 | 1.42 | 12870 | 536 | 6/6 | 998 |
| 5m | all | fvg | bias | fix2 | 2981 | 46.0 | 1.22 | 10992 | 458 | 5/6 | -461 |
| 5m | all | ob | bias | fix3 | 2340 | 51.6 | 1.29 | 9264 | 386 | 6/6 | 274 |
| 5m | all | ob | bias | struct | 2340 | 51.6 | 1.29 | 9264 | 386 | 6/6 | 274 |
| 15m | all | ob | bias | fix2 | 730 | 49.6 | 1.66 | 6700 | 279 | 6/6 | 789 |
| 5m | all | fvg | bias | fix3 | 3241 | 50.9 | 1.13 | 6583 | 274 | 5/6 | -979 |
| 5m | all | fvg | bias | struct | 3241 | 50.9 | 1.13 | 6583 | 274 | 5/6 | -979 |
| 5m | asian | fvg | bias | fix2 | 1138 | 48.2 | 1.35 | 6251 | 260 | 6/6 | 173 |
| 15m | all | ob | bias | fix3 | 860 | 53.7 | 1.55 | 6025 | 251 | 6/6 | 438 |
| 15m | all | ob | bias | struct | 860 | 53.7 | 1.55 | 6025 | 251 | 6/6 | 438 |
| 5m | all | ob | pd+bias | fix2 | 1531 | 43.7 | 1.22 | 5435 | 226 | 5/6 | -66 |
| 5m | london+ny | ob | bias | fix2 | 1151 | 44.9 | 1.3 | 5310 | 221 | 6/6 | 200 |
| 5m | london+ny | fvg | bias | fix2 | 1232 | 46.3 | 1.25 | 4972 | 207 | 5/6 | -695 |
| 15m | all | fvg | bias | fix2 | 1161 | 45.1 | 1.23 | 4466 | 186 | 6/6 | 319 |
| 5m | asian | fvg | bias | fix3 | 1220 | 53.0 | 1.25 | 4393 | 183 | 5/6 | -89 |
| 5m | asian | fvg | bias | struct | 1220 | 53.0 | 1.25 | 4393 | 183 | 5/6 | -89 |
| 5m | asian | ob | bias | fix2 | 1029 | 44.8 | 1.26 | 4250 | 177 | 5/6 | -244 |
| 5m | ny | ob | bias | fix2 | 760 | 45.5 | 1.33 | 3907 | 163 | 5/6 | -181 |
| 5m | london+ny | ob | bias | fix3 | 1263 | 49.9 | 1.21 | 3730 | 155 | 6/6 | 76 |
| 5m | london+ny | ob | bias | struct | 1263 | 49.9 | 1.21 | 3730 | 155 | 6/6 | 76 |
| 1h | all | fvg | bias | fix3 | 308 | 51.6 | 1.83 | 3612 | 150 | 6/6 | 162 |
| 1h | all | fvg | bias | struct | 308 | 51.6 | 1.83 | 3612 | 150 | 6/6 | 162 |
| 5m | ny | fvg | bias | fix2 | 722 | 47.1 | 1.29 | 3427 | 143 | 5/6 | -579 |
| 15m | all | ob | pd+bias | fix2 | 489 | 46.6 | 1.47 | 3396 | 142 | 6/6 | 112 |
| 15m | all | fvg | bias | fix3 | 1230 | 48.9 | 1.18 | 3345 | 139 | 6/6 | 151 |


## 4. Which dimensions tend to work?


**By setup:**

| setup | configs | robust | median_net$ |
| --- | --- | --- | --- |
| fvg | 180 | 54 | 647 |
| ob | 360 | 63 | 46 |
| sweep | 135 | 1 | -966 |


**By session:**

| session | configs | robust | median_net$ |
| --- | --- | --- | --- |
| all | 135 | 45 | 543 |
| asian | 135 | 13 | 41 |
| london | 135 | 7 | -76 |
| london+ny | 135 | 28 | 140 |
| ny | 135 | 25 | 211 |


**By timeframe:**

| tf | configs | robust | median_net$ |
| --- | --- | --- | --- |
| 15m | 225 | 32 | -14 |
| 1h | 225 | 37 | 145 |
| 5m | 225 | 49 | -70 |


**By target:**

| target | configs | robust | median_net$ |
| --- | --- | --- | --- |
| fix2 | 225 | 48 | 132 |
| fix3 | 225 | 35 | 73 |
| struct | 225 | 35 | 73 |
