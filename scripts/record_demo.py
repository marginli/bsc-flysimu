"""錄 DEMO 用的遊戲影片與逐格神經活動（fruitfly-lab，ViZDoom 1.3.0）。

和 fly_doom.py 用同一個大脑、編碼、讀出規則、種子（seed=0 的第 0 局），只多記錄每格的擊殺數、
所有敵人方位與原始畫面，畫面直接送進 ffmpeg 存成 mp4。輸出只寫到實跑資料夾的 demo/rec/，不動 repo 內的結果。
用法：PYTHONNOUSERSITE=1 ~/anaconda3/envs/ffl_doom130/bin/python scripts/record_demo.py [條件 ...]
接著跑 scripts/build_data.py，把影片與逐格資料整理進 assets/demo/（PART 6 用）。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import vizdoom as vzd

WORK = Path.home() / "claude_bscai" / "fly_play_game"     # 本機的重現實跑資料夾（PART 2 的下載包解開後也是同樣的結構）
FF = WORK / "fruitfly_lab"
sys.path.insert(0, str(FF / "repo" / "doom"))
import fly_doom as fd  # noqa: E402

OUT = WORK / "demo" / "rec"
CAL = FF / "results" / "local_doom_vizdoom130"     # 本機 1.3.0 校準（與作者相同）
FFMPEG = Path.home() / "anaconda3" / "bin" / "ffmpeg"


def record(policy, seed=0):
    fd.RESULTS = OUT / "cal"
    circuit = fd.Circuit()
    game = fd.new_game(False, seed)
    act, _ = fd.make_policy(policy, circuit, seed)
    game.new_episode()
    h, w = game.get_screen_height(), game.get_screen_width()
    enc = subprocess.Popen([str(FFMPEG), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{w}x{h}", "-r", "35", "-i", "-", "-vf", "scale=iw*2:ih*2:flags=neighbor",
                            "-c:v", "libopenh264", "-b:v", "1200k", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                            str(OUT / f"{policy}.mp4")], stdin=subprocess.PIPE)
    tics = []
    while not game.is_episode_finished():
        st = game.get_state()
        targets = fd.enemies(st)
        action, rates = act(targets)
        enc.stdin.write(st.screen_buffer.tobytes())
        tics.append({"t": st.number, "k": int(game.get_game_variable(vzd.GameVariable.KILLCOUNT)),
                     "e": [round(az, 1) for az, _ in targets], "a": action,
                     "r": {k: round(v, 1) for k, v in rates.items()} if rates else None})
        game.make_action(action)
    kills = int(game.get_game_variable(vzd.GameVariable.KILLCOUNT))
    game.close()
    enc.stdin.close()
    enc.wait()
    (OUT / f"{policy}.json").write_text(json.dumps({"policy": policy, "seed": seed, "kills": kills, "tics": tics},
                                                  separators=(",", ":")))
    print(f"{policy}: kills={kills} tics={len(tics)}", flush=True)
    return kills


if __name__ == "__main__":
    (OUT / "cal").mkdir(parents=True, exist_ok=True)
    for f in ("calibration_fly.json", "calibration_scrambled.json"):
        shutil.copy(CAL / f, OUT / "cal" / f)
    for p in sys.argv[1:] or ["fly", "lesion025", "scrambled_cal"]:
        record(p)
