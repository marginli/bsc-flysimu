"""FF1：核對 Shiu 全腦模型附的 FlyWire 連線表（Connectivity_783.parquet）。
只給一個檔案：印出神經元數、連結數、突觸總數。
再給第二個檔案（另外下載的 FlyWire proofread_connections_783.feather）：逐條比對兩份是否相同。"""
import json
import sys

import pandas as pd

shiu = pd.read_parquet(sys.argv[1])
out = {"shiu_edges": len(shiu), "shiu_synapses": int(shiu.Connectivity.sum()),
       "shiu_neurons": int(pd.unique(pd.concat([shiu.Presynaptic_ID, shiu.Postsynaptic_ID])).size)}
if len(sys.argv) > 2:
    loc = pd.read_feather(sys.argv[2])
    pre = [c for c in loc.columns if "pre" in c.lower() and "id" in c.lower()][0]
    post = [c for c in loc.columns if "post" in c.lower() and "id" in c.lower()][0]
    cnt = [c for c in loc.columns if "syn" in c.lower() and "count" in c.lower()][0]
    agg = loc.groupby([pre, post])[cnt].sum().reset_index()      # 同一對神經元在不同神經氈的列合併
    out.update({"local_rows": len(loc), "local_edges_after_neuropil_merge": len(agg),
                "local_synapses": int(agg[cnt].sum()),
                "local_neurons": int(pd.unique(pd.concat([agg[pre], agg[post]])).size)})
    m = shiu.merge(agg, left_on=["Presynaptic_ID", "Postsynaptic_ID"], right_on=[pre, post], how="outer", indicator=True)
    out["only_shiu"] = int((m._merge == "left_only").sum())
    out["only_local"] = int((m._merge == "right_only").sum())
    both = m[m._merge == "both"]
    out["both"] = len(both)
    out["count_equal_frac"] = float((both.Connectivity == both[cnt]).mean())
print(json.dumps(out, indent=1))
