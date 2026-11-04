#!/usr/bin/env python3
"""Issue #97: split request-stage2-97-fix1.json into 18 single-corner requests.

The one-job 18-corner request hit the fleet 3600 s whole-job ceiling (serial
upper bound 32520 s). One request per corner (process x T x VDD) runs each on
its own job via `klt sim --batch-set`. Output: request-stage2-97-s-<P>-<T>-<V>.json
"""
import json, copy
base = json.load(open("request-stage2-97-fix1.json"))
for p in base["corners"]["process"]:
    for t in base["corners"]["temperature_c"]:
        for v in base["corners"]["params"]["vddv"]:
            r = copy.deepcopy(base)
            r["corners"]["process"] = [p]
            r["corners"]["temperature_c"] = [t]
            r["corners"]["params"]["vddv"] = [v]
            r["_comment"] = r["_comment"][:4] + [
                f"Issue #97 single-corner shard: {p['name']} {t} C {v} V, ramped start-up, timeout_s 1800, one fleet job per corner."]
            json.dump(r, open(f"request-stage2-97-s-{p['name']}-{t}-{v}.json", "w"), indent=1)
