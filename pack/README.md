# 果蠅大腦玩 Doom：程式包

BSC 專題課程〈果蠅大腦玩 Doom：重現 fruitfly-lab〉的下載包。
網頁：https://marginli.github.io/bsc-flysimu/ （PART 2 有逐步說明）

這一包只有本課自己寫的程式。被重現的 repo 由 `run_all.sh` 自己 clone，資料也由它下載：

| 被重現的 repo | 固定的版本 | 授權 |
|---|---|---|
| https://github.com/webergithub/fruitfly-lab | commit 8c27fe8 | repo 裡沒有授權檔，所以本包不附它的任何檔案 |
| https://github.com/philshiu/Drosophila_brain_model | 最新版（--depth 1） | MIT |

## 兩個指令

```
bash setup_envs.sh              # 建三個 conda 環境（只需一次）
bash fruitfly_lab/run_all.sh    # FF1–FF6、ViZDoom 1.3.2 對照、加做檢查 E1–E4
```

`run_all.sh` 跑完會自動執行 `check.py`，逐項對照 `expected.json`（本課實跑的結果），
最後一行印出「幾項通過、幾項不符」。

## 目錄

| 路徑 | 內容 |
|---|---|
| `setup_envs.sh` | 建環境，套件版本照本課實跑時固定 |
| `check.py`、`expected.json` | 驗收程式與預期值 |
| `fruitfly_lab/run_all.sh` | 一鍵重跑 |
| `fruitfly_lab/ext/` | 加做檢查的程式（只匯入作者的程式，不修改它） |

跑完之後，每一步的終端輸出在 `fruitfly_lab/logs/`，數字在 `fruitfly_lab/results/`。

## 需要什麼

Linux 或 macOS、conda（Anaconda 或 Miniconda）、git、curl、網路。不需要 GPU。
所有指令都會設 `PYTHONNOUSERSITE=1`，讓家目錄 `~/.local` 裡的套件不會混進環境。

教學用途，非營利。
