"""M, A table for the P = 8/9 prescaler (issue #158): N = P*M + A with P = 8, i.e. N = 8*M + A.

The prescaler divides by 9 for A prescaler cycles and by 8 for M - A cycles, so one output period of the post-
prescaler counters is 9*A + 8*(M - A) = 8*M + A VCO cycles. Every N is reachable with M = N // 8, A = N % 8 provided
A <= M (the swallow counter cannot count more cycles than the main counter) and A <= 7 (spec row 3).
This is arithmetic, not a simulation result.
"""
import sys

P = 8
A_MAX = 7
N_LO, N_HI = 90, 110


def split(n, p=P):
    """Return (M, A) with n = p*M + A, 0 <= A < p."""
    return n // p, n % p


def total_cycles(m, a, p=P):
    """VCO cycles in one counter period: A cycles at /(p+1), M - A at /p."""
    return a * (p + 1) + (m - a) * p


def check(lo=N_LO, hi=N_HI, p=P):
    rows = []
    for n in range(lo, hi + 1):
        m, a = split(n, p)
        ok = a <= m and a <= A_MAX and total_cycles(m, a, p) == n
        rows.append((n, m, a, ok))
    return rows


def main():
    rows = check()
    print("| N | f_out at 50 MHz ref (GHz) | M | A | A <= M | A <= 7 | 8(M-A)+9A = N |")
    print("|---|---|---|---|---|---|---|")
    for n, m, a, ok in rows:
        print("| %d | %.2f | %d | %d | %s | %s | %s |" % (
            n, n * 0.05, m, a, "yes" if a <= m else "NO", "yes" if a <= A_MAX else "NO",
            "yes" if total_cycles(m, a) == n else "NO"))
    bad = [r for r in rows if not r[3]]
    print("\n%d values, %d fail" % (len(rows), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
