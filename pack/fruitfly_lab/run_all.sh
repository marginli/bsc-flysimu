#!/usr/bin/env bash
# fruitfly-lab 一鍵重跑：FF1–FF6 ＋ ViZDoom 1.3.2 對照 ＋ 加做檢查 E1–E4。用法：bash run_all.sh（本課實測 14 分 34 秒，12 核 CPU，與 blackjack 同時跑）
# 需要先跑過上一層的 setup_envs.sh。下載約 400 MB（Shiu 全腦模型 repo ＋ FlyWire 註解檔）。
# 若另外下載了 FlyWire 的 proofread_connections_783.feather，可設 FLYWIRE_FEATHER=<路徑> 讓 FF1 逐條比對。
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ENVS="$(conda info --base)/envs"
B=$ENVS/ffl_brian/bin/python      # Brian2 全腦模型、抽子圖
D=$ENVS/ffl_doom130/bin/python    # ViZDoom 1.3.0：與作者逐局相同
D2=$ENVS/ffl_doom/bin/python      # ViZDoom 1.3.2：版本對照
export PYTHONNOUSERSITE=1
cd "$HERE"
[ -d repo ] || git clone -q https://github.com/webergithub/fruitfly-lab.git repo
git -C repo checkout -q 8c27fe8e70903e09b1d87bae6989051d09161e92
[ -d repo/Drosophila_brain_model ] || git clone -q --depth 1 https://github.com/philshiu/Drosophila_brain_model.git repo/Drosophila_brain_model
mkdir -p logs results repo/data
cd repo
mkdir -p ../results/author_doom && cp doom/results/*.json ../results/author_doom/ && cp output/validation.json ../results/validation_author.json   # 作者附的結果，留作對照
[ -f data/flywire_annotations_783.tsv ] || curl -sL -o data/flywire_annotations_783.tsv https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/supplemental_files/Supplemental_file1_neuron_annotations.tsv
echo "FF1 資料核對";      $B ../ext/ff1_compare_conn.py Drosophila_brain_model/Connectivity_783.parquet $FLYWIRE_FEATHER > ../results/ff1_conn.json 2> ../logs/ff1_conn.log
echo "FF2 抽子圖";        md5sum circuit/* > ../logs/ff2_md5_committed.txt; $B flycircuit/extract.py > ../logs/ff2_extract.log 2>&1; md5sum circuit/* > ../logs/ff2_md5_rerun.txt
echo "FF3 子圖 vs 全腦（約 6 分鐘，會用滿 CPU）"; $B flycircuit/validate.py > ../logs/ff3_validate.log 2>&1; cp output/validation.json ../results/validation_local.json
echo "FF4 校準";          $D doom/fly_doom.py --calibrate > ../logs/ff4_calibrate.log 2>&1
for v in 132 130; do       # 先跑 1.3.2 對照、最後跑 1.3.0，讓 doom/results/ 停在與作者相同的版本
  P=$([ $v = 130 ] && echo $D || echo $D2)
  echo "FF5 七個條件 × 10 局（ViZDoom 1.3.${v#13}）"
  for p in fly scrambled scrambled_cal lesion lesion025 random oracle; do $P doom/fly_doom.py --policy $p --episodes 10 > ../logs/ff5_${p}_v$v.log 2>&1; done
  echo "FF6 統計";        $P doom/analyze.py > ../logs/ff6_analyze_v$v.log 2>&1
  mkdir -p ../results/local_doom_vizdoom$v && cp doom/results/*.json ../results/local_doom_vizdoom$v/
done
echo "E1–E3 加做檢查（ViZDoom 1.3.0 ＋ 1.3.2）"; $D ../ext/ff_extra.py E1 E2 E3 > ../logs/ext_vizdoom130.log 2>&1; $D2 ../ext/ff_extra.py E1 > ../logs/ext_vizdoom132.log 2>&1
echo "E4 右側不對稱";     $B ../ext/e4_asymmetry.py > ../logs/e4_asymmetry.log 2>&1
git checkout -q _vizdoom.ini doom/results output 2>/dev/null || true   # 還原作者附的檔案；本機結果都在 ../results/
cd "$HERE"; "$D" ../check.py fruitfly
