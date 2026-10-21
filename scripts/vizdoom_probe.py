"""ViZDoom 關卡 defend_the_center 的計時方式（PART 5 第 1 節：作者紀錄的局長為什麼比錄影多 10 格）。
讀關卡設定檔的 episode_start_time、episode_timeout，並實際開一局：記下第一個畫面時的 get_episode_time()，
再整局都不按鍵，數做了幾次決定、結束時的 get_episode_time()、是不是玩家死亡。
作者 fly_doom.py 的局長（out/fruitfly/*/<policy>.json 的 tics）就是結束時的 get_episode_time()。
用法：~/anaconda3/envs/ffl_doom/bin/python scripts/vizdoom_probe.py   （輸出 out/vizdoom_probe.json）"""
import json
import os

import vizdoom as vzd

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(vzd.scenarios_path, "defend_the_center.cfg")

cfg = {}
for line in open(CFG):
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = (x.strip() for x in line.split("=", 1))
        cfg[k] = v

g = vzd.DoomGame()
g.load_config(CFG)
g.set_window_visible(False)
g.set_mode(vzd.Mode.PLAYER)
g.set_seed(0)
g.init()
g.new_episode()
first = g.get_episode_time()
n = 0
while not g.is_episode_finished():
    g.make_action([0, 0, 0])
    n += 1
out = {
    "_note": "scripts/vizdoom_probe.py 產生；ViZDoom " + vzd.__version__,
    "cfg": {"episode_start_time": int(cfg["episode_start_time"]), "episode_timeout": int(cfg["episode_timeout"]),
            "timeout_s": round(int(cfg["episode_timeout"]) / 35, 1)},
    "episode_time_at_first_state": first,
    "noop_episode": {"seed": 0, "decisions": n, "final_episode_time": g.get_episode_time(), "player_dead": g.is_player_dead()},
}
g.close()
json.dump(out, open(os.path.join(D, "out/vizdoom_probe.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False))
