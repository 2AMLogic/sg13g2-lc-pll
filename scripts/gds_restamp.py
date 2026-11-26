"""Shift the seconds field of every GDS BGNLIB/BGNSTR timestamp: a byte churn with no geometry."""
import sys

src, dst = sys.argv[1], sys.argv[2]
data = bytearray(open(src, "rb").read())
i, n, hits = 0, len(data), 0
while i + 4 <= n:
    rlen = int.from_bytes(data[i:i + 2], "big")
    if rlen < 4:
        break
    # record type 0x01 = BGNLIB, 0x05 = BGNSTR; data type 0x02 = INT2; 12 int2 = mod/access y m d h m s
    if data[i + 3] == 0x02 and data[i + 2] in (0x01, 0x05) and rlen >= 28:
        for off in (i + 14, i + 26):            # the two seconds fields
            data[off:off + 2] = ((int.from_bytes(data[off:off + 2], "big") + 7) % 60).to_bytes(2, "big")
        hits += 1
    i += rlen
if hits == 0:
    sys.exit("gds-restamp: no BGNLIB/BGNSTR record found in " + src + "; refusing")
open(dst, "wb").write(bytes(data))
print("gds-restamp: re-stamped " + str(hits) + " records")
