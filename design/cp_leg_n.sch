v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: cp_leg_n -- charge-pump NMOS sink leg: mirror + cascode + dual steering switches
Topology from sg13g2-pll cp_leg_n (83e59fe); mirror/cascode retargeted to I_cp = 200 uA nominal at IREF = 20 uA.
DN high steers the leg to VOUT; DNB high dumps it to VDUMP.
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
C {sg13g2_pr/sg13_hv_nmos.sym} 0 0 0 0 {name=M1 model=sg13_hv_nmos w=3.8u l=1u ng=1 m=10 spiceprefix=X}
C {lab_pin.sym} -20 0 0 0 {name=l1 lab=IBN}
C {lab_pin.sym} 20 -30 2 0 {name=l2 lab=tail}
C {lab_pin.sym} 20 30 2 0 {name=l3 lab=VSS}
C {lab_pin.sym} 20 0 2 0 {name=l4 lab=VSS}
C {sg13g2_pr/sg13_hv_nmos.sym} 0 300 0 0 {name=M2 model=sg13_hv_nmos w=3.8u l=1u ng=1 m=10 spiceprefix=X}
C {lab_pin.sym} -20 300 0 0 {name=l5 lab=ICN}
C {lab_pin.sym} 20 270 2 0 {name=l6 lab=sw}
C {lab_pin.sym} 20 330 2 0 {name=l7 lab=tail}
C {lab_pin.sym} 20 300 2 0 {name=l8 lab=VSS}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 600 0 0 {name=SWO model=sg13_hv_nmos w=6u l=0.3u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} 280 600 0 0 {name=l9 lab=DN}
C {lab_pin.sym} 320 570 2 0 {name=l10 lab=VOUT}
C {lab_pin.sym} 320 630 2 0 {name=l11 lab=sw}
C {lab_pin.sym} 320 600 2 0 {name=l12 lab=VSS}
C {sg13g2_pr/sg13_hv_nmos.sym} 0 600 0 0 {name=SWD model=sg13_hv_nmos w=6u l=0.3u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} -20 600 0 0 {name=l13 lab=DNB}
C {lab_pin.sym} 20 570 2 0 {name=l14 lab=VDUMP}
C {lab_pin.sym} 20 630 2 0 {name=l15 lab=sw}
C {lab_pin.sym} 20 600 2 0 {name=l16 lab=VSS}
C {ipin.sym} -900 -200 0 0 {name=p1 lab=IBN}
C {ipin.sym} -900 -100 0 0 {name=p2 lab=ICN}
C {ipin.sym} -900 0 0 0 {name=p3 lab=DN}
C {ipin.sym} -900 100 0 0 {name=p4 lab=DNB}
C {opin.sym} 900 200 0 0 {name=p5 lab=VOUT}
C {opin.sym} 900 300 0 0 {name=p6 lab=VDUMP}
C {iopin.sym} -900 400 0 0 {name=p7 lab=VSS}
