#!/usr/bin/env bash
# 建立重現需要的四個 conda 環境（只需做一次，約 10 分鐘，需要網路）。用法：bash setup_envs.sh
# 版本照本課實跑時的環境固定；ViZDoom 1.3.0 是 fruitfly-lab 作者用的版本，換版本遊戲隨機抽樣會不同。
set -e
CONDA_BASE="$(conda info --base)"
export PYTHONNOUSERSITE=1        # 不讓使用者家目錄 ~/.local 裡的套件混進環境
# conda 預設的 libmamba 求解器在某些安裝裡會壞掉（錯誤訊息含 libmambapy），失敗時改用 classic 求解器再試一次
mk() { conda env list | grep -q "^$1 " || conda create -y -q -n "$1" "python=$2" || conda create -y -q --solver classic -n "$1" "python=$2"
       "$CONDA_BASE/envs/$1/bin/pip" install -q "${@:3}"; }
mk flyplay_bj  3.11 numpy==2.4.6 scipy==1.17.1 pandas==3.0.6
mk ffl_brian   3.11 Brian2==2.9.0 numpy==1.26.4 pandas==2.3.3 pyarrow==17.0.0 joblib numba==0.68.0
mk ffl_doom130 3.12 vizdoom==1.3.0 numpy==2.5.4 pandas==3.0.6 pyarrow==26.0.0 numba==0.68.0 pillow
mk ffl_doom    3.12 vizdoom==1.3.2 numpy==2.5.4 pandas==3.0.6 pyarrow==26.0.0 numba==0.68.0 pillow
for e in flyplay_bj ffl_brian ffl_doom130 ffl_doom; do "$CONDA_BASE/envs/$e/bin/python" -c "import sys; print('$e', sys.version.split()[0], 'OK')"; done
