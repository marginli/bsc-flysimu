#!/usr/bin/env bash
# fly-blackjack 一鍵重跑：BJ1–BJ5 ＋ 加做檢查 X1–X4。用法：bash run_all.sh（本課實測 21 分 54 秒，12 核 CPU，與 fruitfly_lab 同時跑）
# 需要先跑過上一層的 setup_envs.sh。每步的終端輸出寫到 logs/，數字寫到 results/，最後由 ../check.py 驗收。
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$(conda info --base)/envs/flyplay_bj/bin/python"
export PYTHONNOUSERSITE=1 PYTHONPATH=.
cd "$HERE"
[ -d repo ] || git clone -q https://github.com/WilliamJones/fly-blackjack.git repo
git -C repo checkout -q 004b2e3e9ccb742f83c5bdc2717c97f5a64b420f
mkdir -p logs results
cd repo
echo "BJ1 Dino";                  $PY -m flybrain.train --generations 40 --population 48 --seconds 30 --out ../results/bj1_checkpoint.json > ../logs/bj1_train.log 2>&1
echo "BJ2 下載並切出蕈狀體（下載約 107 MB）"; $PY -m flybrain.mb.fetch > ../logs/bj2_fetch.log 2>&1
for i in 1 2; do $PY -m flybrain.mb.extract > ../logs/bj2_extract_run$i.log 2>&1; md5sum data/mb_circuit.npz; done | tee ../logs/bj2_md5.txt
echo "BJ3 制約與 T-maze";         $PY -m flybrain.mb.experiment > ../logs/bj3_experiment.log 2>&1; $PY -m flybrain.mb.tmaze > ../logs/bj3_tmaze.log 2>&1; cp data/mb_results.json data/mb_tmaze.json ../results/
echo "BJ4 覓食（照 README 重新訓練）"; $PY ../scripts/bj4_forage.py > ../logs/bj4_forage.log 2>&1
echo "BJ4b 覓食（seconds=45 重新訓練）"; $PY ../scripts/bj4b_forage_s45.py > ../logs/bj4b_forage_s45.log 2>&1
echo "BJ5 21 點";                 $PY ../scripts/bj5_blackjack.py 30000 0 1 2 > ../logs/bj5_blackjack.log 2>&1
echo "BJ5b 評分作者附的大腦";     $PY ../scripts/bj5b_author_brain.py > ../logs/bj5b_author_brain.log 2>&1
echo "加做檢查 X1–X4";            $PY ../scripts/bj_extra.py > ../logs/bj_extra.log 2>&1
cd "$HERE"; "$PY" ../check.py blackjack
