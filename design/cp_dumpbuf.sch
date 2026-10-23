v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: cp_dumpbuf -- VDUMP tracking follower (a leg that is steered away dumps here)
NMOS source follower from VOUT plus an IBIAS-mirrored sink (x5 the unit, ~100 uA at IREF = 20 uA).
Device flavour: SG13G2 3.3 V thick-oxide CMOS (sg13_hv_nmos / sg13_hv_pmos), as the adopted
sg13g2-pll PFD. Connectivity is label-driven (lab_pin stubs on every terminal), the same
convention as sg13g2-pll's schematics. Sizing is simulation-grounded only at the typical
corner and nominal supply (sim/cp-dc/); no corner grid yet.
}
G {}
K {}
V {}
S {}
E {}
C {sg13g2_pr/sg13_hv_nmos.sym} 0 0 0 0 {name=M1 model=sg13_hv_nmos w=6u l=0.5u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} -20 0 0 0 {name=l1 lab=VOUT}
C {lab_pin.sym} 20 -30 2 0 {name=l2 lab=VDD}
C {lab_pin.sym} 20 30 2 0 {name=l3 lab=VDUMP}
C {lab_pin.sym} 20 0 2 0 {name=l4 lab=VSS}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 0 0 0 {name=M2 model=sg13_hv_nmos w=4u l=1u ng=1 m=5 spiceprefix=X}
C {lab_pin.sym} 280 0 0 0 {name=l5 lab=IBIAS}
C {lab_pin.sym} 320 -30 2 0 {name=l6 lab=VDUMP}
C {lab_pin.sym} 320 30 2 0 {name=l7 lab=VSS}
C {lab_pin.sym} 320 0 2 0 {name=l8 lab=VSS}
C {ipin.sym} -900 -200 0 0 {name=p1 lab=VOUT}
C {ipin.sym} -900 -100 0 0 {name=p2 lab=IBIAS}
C {opin.sym} 900 0 0 0 {name=p3 lab=VDUMP}
C {iopin.sym} -900 100 0 0 {name=p4 lab=VDD}
C {iopin.sym} -900 200 0 0 {name=p5 lab=VSS}
