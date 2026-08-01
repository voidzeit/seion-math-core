#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thin CLI entrypoint for the seion_kgr package (mirrors seion_train_v25.py's
repo-root-script convention). See seion_kgr/train.py for the real logic and
docs/SEION_KGR_MATHEMATICAL_CONTRACT.md for what each flag corresponds to.

    python seion_kgr_v26_train.py --self_test
    python seion_kgr_v26_train.py --train data/FB15K-237/train.txt --valid data/FB15K-237/valid.txt \\
        --test data/FB15K-237/test.txt --out_dir runs/KGR_V26_SMOKE --epochs 1 --cpu
"""
from seion_kgr.train import main

if __name__ == "__main__":
    main()
