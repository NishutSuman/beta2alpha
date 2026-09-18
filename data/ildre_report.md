# ILDRE condition backtest (2y, 8-fold walk-forward, costs)

**36 configs · 4 robust (>= 9/10 folds, net>0).**

## Top results
| tf | cond | tp | sess | trades | win% | PF | net$ | /mo | folds+ | worst | robust |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 15m | nested | fix2 | all | 822 | 47.4 | 1.34 | 4405 | 72 | 9/10 | -189 | True |
| 15m | nested+xsweep | fix2 | all | 818 | 46.6 | 1.29 | 3854 | 63 | 9/10 | -99 | True |
| 15m | nested | dest | all | 851 | 61.2 | 1.36 | 3561 | 59 | 9/10 | -251 | True |
| 15m | nested+xsweep | dest | all | 849 | 60.5 | 1.31 | 3135 | 52 | 9/10 | -161 | True |
| 15m | base (bias+pd) | fix2 | all | 1136 | 47.4 | 1.31 | 5709 | 94 | 8/10 | -369 | False |
| 15m | base (bias+pd) | dest | all | 1207 | 60.6 | 1.28 | 4087 | 67 | 5/10 | -332 | False |
| 15m | base (bias+pd) | fix2 | london+ny | 838 | 46.2 | 1.25 | 3457 | 57 | 7/10 | -340 | False |
| 15m | base (bias+pd) | dest | london+ny | 868 | 60.7 | 1.28 | 2876 | 47 | 7/10 | -179 | False |
| 15m | xsweep+fvg (no nest) | fix2 | all | 733 | 46.1 | 1.23 | 2843 | 47 | 8/10 | -401 | False |
| 15m | nested+fvg | fix2 | all | 555 | 46.5 | 1.28 | 2475 | 41 | 8/10 | -142 | False |
| 15m | xsweep+fvg (no nest) | fix2 | london+ny | 472 | 47.9 | 1.32 | 2413 | 40 | 8/10 | -76 | False |
| 15m | xsweep+fvg (no nest) | dest | all | 737 | 61.2 | 1.28 | 2412 | 40 | 7/10 | -200 | False |
| 15m | nested+xsweep+fvg | fix2 | all | 541 | 46.0 | 1.25 | 2226 | 37 | 8/10 | -150 | False |
| 15m | nested+xsweep | fix2 | london+ny | 521 | 45.3 | 1.22 | 1901 | 31 | 8/10 | -362 | False |
| 15m | nested+xsweep | dest | london+ny | 535 | 60.7 | 1.3 | 1892 | 31 | 7/10 | -314 | False |
| 15m | nested | dest | london+ny | 546 | 60.6 | 1.29 | 1879 | 31 | 7/10 | -234 | False |
| 15m | nested | fix2 | london+ny | 534 | 45.1 | 1.21 | 1874 | 31 | 8/10 | -307 | False |
| 15m | nested+fvg | dest | all | 560 | 59.6 | 1.24 | 1624 | 27 | 7/10 | -157 | False |
| 15m | nested+xsweep+fvg | dest | all | 547 | 59.8 | 1.23 | 1551 | 26 | 7/10 | -180 | False |
| 15m | xsweep+fvg (no nest) | dest | london+ny | 473 | 61.5 | 1.26 | 1424 | 23 | 6/10 | -58 | False |
| 15m | nested+xsweep+extreme | fix2 | all | 571 | 42.6 | 1.13 | 1223 | 20 | 7/10 | -376 | False |
| 15m | nested+extreme | fix2 | all | 575 | 42.4 | 1.12 | 1180 | 19 | 8/10 | -436 | False |
| 15m | nested+xsweep+extreme | dest | all | 583 | 56.3 | 1.15 | 1124 | 18 | 8/10 | -238 | False |
| 15m | nested+extreme | dest | all | 587 | 56.0 | 1.15 | 1100 | 18 | 8/10 | -298 | False |
| 15m | nested+xsweep+fvg | fix2 | london+ny | 317 | 45.1 | 1.19 | 1019 | 17 | 7/10 | -43 | False |
| 15m | nested+xsweep+extreme | dest | london+ny | 308 | 58.8 | 1.26 | 972 | 16 | 7/10 | -91 | False |
| 15m | nested+extreme | dest | london+ny | 309 | 58.6 | 1.25 | 941 | 15 | 7/10 | -91 | False |
| 15m | nested+fvg | fix2 | london+ny | 335 | 44.2 | 1.15 | 858 | 14 | 6/10 | -101 | False |
| 15m | nested+xsweep+fvg | dest | london+ny | 319 | 60.2 | 1.21 | 815 | 13 | 7/10 | -121 | False |
| 15m | nested+fvg | dest | london+ny | 335 | 59.1 | 1.17 | 690 | 11 | 6/10 | -82 | False |
| 15m | nested+xsweep+fvg+extreme | dest | all | 307 | 56.7 | 1.16 | 627 | 10 | 5/10 | -203 | False |
| 15m | nested+xsweep+extreme | fix2 | london+ny | 301 | 41.5 | 1.07 | 352 | 6 | 6/10 | -352 | False |
| 15m | nested+extreme | fix2 | london+ny | 302 | 41.4 | 1.06 | 321 | 5 | 6/10 | -352 | False |
| 15m | nested+xsweep+fvg+extreme | fix2 | all | 303 | 41.3 | 1.05 | 261 | 4 | 6/10 | -347 | False |
| 15m | nested+xsweep+fvg+extreme | dest | london+ny | 146 | 56.8 | 1.13 | 253 | 4 | 6/10 | -89 | False |
| 15m | nested+xsweep+fvg+extreme | fix2 | london+ny | 144 | 38.9 | 0.93 | -182 | -3 | 5/10 | -214 | False |
