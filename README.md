# 果蠅大腦玩 Doom：重現 fruitfly-lab

BSC 專題課程（**重現型**，規範見 `../types/repro.md`）。對象是公開的果蠅連結體模擬專案
[fruitfly-lab](https://github.com/webergithub/fruitfly-lab)（commit 8c27fe8）。
2026-10-16 之前這個 repo 同時講 fly-blackjack；那部分已拆成獨立的課 `../fly_blackjack/`（repo bsc-flyblackjack）。

線上版：https://marginli.github.io/bsc-flysimu/ （`robots.txt` 擋掉搜尋引擎索引）

## 頁面

| 頁面 | 內容 |
|---|---|
| `index.html` | 首頁 |
| `part1-what.html` | PART 1　fruitfly-lab 在做什麼：四個零件，哪些來自資料、哪些是人為設定 |
| `part2-setup.html` | PART 2　準備環境與資料 |
| `part3-fruitfly.html` | PART 3　重現 fruitfly-lab（FF1–FF6）；三種判定標準的定義處 |
| `part4-checks.html` | PART 4　作者沒做的檢查（E1–E4） |
| `part5-demo.html` | PART 5　逐格看迴路怎麼打（互動播放） |
| `encode.html` | PART 1 圖 4（輸入編碼）的單獨頁，給簡報嵌入或離線開；由 `scripts/make_encode_anim.py` 產生 |
| `part6-code.html` | PART 6　讀程式：一鍵重跑叫到的每一支程式，三層（shell → Python → lif.py）；程式區塊由 `scripts/make_code.py` 產生 |

## 目錄

| 路徑 | 內容 |
|---|---|
| `assets/flysimu.css` | 共用樣式，與 `VFB/assets/vfb.css`、`LPU/assets/lpu.css`、`hub/assets/bsc.css` 用同一組設計變數 |
| `assets/*.png` | 真實資料圖，由 `scripts/make_figures.py` 產生 |
| `assets/p3-shot-*.png` | PART 3 的遊戲實況截圖，由 `scripts/make_shots.py` 從 `assets/demo/*.mp4` 抽幀；PART 3 的終端機節錄（`<figure class="shot">`）直接貼 `out/*/logs/` 的原文，數字由 `number_audit.py` 對回 |
| `assets/demo/` | PART 5 的三段錄影與逐格資料，由 `scripts/record_demo.py`、`scripts/build_data.py` 產生 |
| `out/` | **頁面上每個數字的出處**：實跑的 JSON 與 log，由 `scripts/collect_out.py` 從本機實跑資料夾收來；`out/code_meta.json` 是 PART 6 用的行數與常數，由 `make_code.py` 從原檔抓 |
| `pack/` | 學員下載包的原始檔（`setup_envs.sh`、`fruitfly_lab/run_all.sh`、加做檢查的程式、`check.py`、`expected.json`） |
| `downloads/flydoom-code.zip` | `pack/` 打包，附 `SHA256SUMS.txt`。改了 `pack/` 任何檔案都要重打包 |
| `lif.html` | PART 1 圖 1（漏電整合發放）的單獨頁，給簡報嵌入或離線開；由 `scripts/make_lif_anim.py` 產生，不要手改 |
| `downloads/lif/` | PART 1 圖 1 的投影片用圖（PNG＋SVG）與 `flydoom-lif.zip`，由 `scripts/make_lif_images.py` 產生 |
| `downloads/encode/` | PART 1 圖 4 的投影片用圖（PNG＋SVG）與 `flydoom-encode.zip`，由 `scripts/make_encode_images.py` 產生 |
| `scripts/` | 收資料、產圖、產驗收表、錄影，四道稽核（`page_audit.py`、`content_audit.py`、`svg_audit.py`、`number_audit.py`，沿用 VFB），以及首頁說明影片的產生器（`video_slides.py` 投影片要點＋旁白稿、`make_video.py`、`video_check.py` 查旁白覆蓋、`video_verify.py` 查影音同步與辨識回填） |
| `_notes/` | 修正紀錄。**進 repo，但由 workflow 的 `rm -rf _notes` 擋在網站之外** |

## 重產

```
~/anaconda3/bin/python scripts/collect_out.py     # 實跑資料夾 → out/
~/anaconda3/bin/python scripts/make_figures.py    # out/ → assets/*.png
python3 scripts/make_shots.py                     # assets/demo/*.mp4 → assets/p3-shot-*.png（PART 3 的遊戲畫面截圖）
python3 scripts/make_expected.py                  # out/ → pack/expected.json，接著重打包 downloads/
python3 scripts/video_check.py                    # 投影片上寫的每一點，旁白有沒有講到
~/.venvs/tts/bin/python scripts/make_video.py     # 重做首頁的說明影片（assets/flydoom-overview.mp4 + .vtt + poster.jpg、out/video_meta.json）
~/.venvs/asr/bin/python scripts/video_verify.py   # 影音同步 + 辨識回填（報告在 _video/verify.txt）
python3 scripts/make_code.py                      # PART 6 的程式區塊：從 pack/ 與本機 clone 的作者 repo 照抄（改了 pack/ 要重跑）；--check 只比對
python3 scripts/encode_fig_data.py                # 作者 fly_doom.py 常數＋LC10a 偏好位置 → out/encode_fig.json
python3 scripts/lif_fig_data.py                   # PART 1 圖 1（漏電整合發放）的資料 → out/lif_fig.json
python3 scripts/make_lif_anim.py                  # PART 1 圖 1 與 lif.html（**圖的文字要改在這支**）
python3 scripts/make_lif_images.py                # 圖 1 的投影片用圖與 downloads/lif/flydoom-lif.zip
python3 scripts/make_encode_anim.py               # PART 1 圖 4 與 encode.html（**圖 4 的文字要改在這支程式裡**）
python3 scripts/make_encode_images.py             # 圖 4 的投影片用圖與 downloads/encode/flydoom-encode.zip
python3 scripts/number_audit.py                   # 頁面數字對回 out/
python3 scripts/page_audit.py                     # 標籤平衡、連結與錨點、中英夾雜
```

實跑資料夾是本機的 `~/claude_bscai/fly_play_game/fruitfly_lab/`，結構與下載包解開後的 `fruitfly_lab/` 相同。

## 授權

fruitfly-lab 的 repo 沒有授權檔，所以本 repo 與下載包**不收它的任何程式碼**；`out/` 只收它附的結果檔（數字）
與 README 中宣稱結果的幾行（`out/upstream/fruitfly_README_claims.json`，標明行號）。
Shiu 等人的全腦模型是 MIT 授權。

教學用途，非營利。
