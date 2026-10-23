v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: cp -- charge pump: UP/DN steering, reference-current bias, source + sink legs, dump buffer
Design source for spec row 6 (I_cp typ 200 uA at IREF = 20 uA; 100-400 uA by scaling IREF 10-40 uA, no on-chip
trim DAC) and row 7 (compliance window measured by sim/cp-dc/; NOT graded against V_hi,req).
Starting topology: sg13g2-pll cp (83e59fe) with the bias generation moved inside (cp_bias) and
IREF as the only bias input. UPB/DNB come from the two inverters below (same sizes as sg13g2-pll inv_hv).
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
C {sg13g2_pr/sg13_hv_pmos.sym} 0 0 0 0 {name=IUP_P model=sg13_hv_pmos w=5u l=0.5u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} -20 0 0 0 {name=l1 lab=UP}
C {lab_pin.sym} 20 -30 2 0 {name=l2 lab=VDD}
C {lab_pin.sym} 20 30 2 0 {name=l3 lab=UPB}
C {lab_pin.sym} 20 0 2 0 {name=l4 lab=VDD}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 0 0 0 {name=IUP_N model=sg13_hv_nmos w=2u l=0.5u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} 280 0 0 0 {name=l5 lab=UP}
C {lab_pin.sym} 320 -30 2 0 {name=l6 lab=UPB}
C {lab_pin.sym} 320 30 2 0 {name=l7 lab=VSS}
C {lab_pin.sym} 320 0 2 0 {name=l8 lab=VSS}
C {sg13g2_pr/sg13_hv_pmos.sym} 600 0 0 0 {name=IDN_P model=sg13_hv_pmos w=5u l=0.5u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} 580 0 0 0 {name=l9 lab=DN}
C {lab_pin.sym} 620 -30 2 0 {name=l10 lab=VDD}
C {lab_pin.sym} 620 30 2 0 {name=l11 lab=DNB}
C {lab_pin.sym} 620 0 2 0 {name=l12 lab=VDD}
C {sg13g2_pr/sg13_hv_nmos.sym} 900 0 0 0 {name=IDN_N model=sg13_hv_nmos w=2u l=0.5u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} 880 0 0 0 {name=l13 lab=DN}
C {lab_pin.sym} 920 -30 2 0 {name=l14 lab=DNB}
C {lab_pin.sym} 920 30 2 0 {name=l15 lab=VSS}
C {lab_pin.sym} 920 0 2 0 {name=l16 lab=VSS}
C {cp_bias.sym} 0 600 0 0 {name=XBIAS}
C {lab_pin.sym} -40 540 0 0 {name=l17 lab=IREF}
C {lab_pin.sym} 40 540 2 0 {name=l18 lab=IBP}
C {lab_pin.sym} 40 580 2 0 {name=l19 lab=ICN}
C {lab_pin.sym} 40 620 2 0 {name=l20 lab=ICP}
C {lab_pin.sym} 0 440 2 0 {name=l21 lab=VDD}
C {lab_pin.sym} 0 760 2 0 {name=l22 lab=VSS}
C {cp_leg_p.sym} 600 600 0 0 {name=XLEGP}
C {lab_pin.sym} 560 540 0 0 {name=l23 lab=IBP}
C {lab_pin.sym} 560 580 0 0 {name=l24 lab=ICP}
C {lab_pin.sym} 560 620 0 0 {name=l25 lab=UP}
C {lab_pin.sym} 560 660 0 0 {name=l26 lab=UPB}
C {lab_pin.sym} 640 540 2 0 {name=l27 lab=VOUT}
C {lab_pin.sym} 640 580 2 0 {name=l28 lab=VDUMP}
C {lab_pin.sym} 600 440 2 0 {name=l29 lab=VDD}
C {cp_leg_n.sym} 1200 600 0 0 {name=XLEGN}
C {lab_pin.sym} 1160 540 0 0 {name=l30 lab=IREF}
C {lab_pin.sym} 1160 580 0 0 {name=l31 lab=ICN}
C {lab_pin.sym} 1160 620 0 0 {name=l32 lab=DN}
C {lab_pin.sym} 1160 660 0 0 {name=l33 lab=DNB}
C {lab_pin.sym} 1240 540 2 0 {name=l34 lab=VOUT}
C {lab_pin.sym} 1240 580 2 0 {name=l35 lab=VDUMP}
C {lab_pin.sym} 1200 760 2 0 {name=l36 lab=VSS}
C {cp_dumpbuf.sym} 1800 600 0 0 {name=XBUF}
C {lab_pin.sym} 1760 540 0 0 {name=l37 lab=VOUT}
C {lab_pin.sym} 1760 580 0 0 {name=l38 lab=IREF}
C {lab_pin.sym} 1840 540 2 0 {name=l39 lab=VDUMP}
C {lab_pin.sym} 1800 440 2 0 {name=l40 lab=VDD}
C {lab_pin.sym} 1800 760 2 0 {name=l41 lab=VSS}
C {ipin.sym} -900 -200 0 0 {name=p1 lab=UP}
C {ipin.sym} -900 -100 0 0 {name=p2 lab=DN}
C {ipin.sym} -900 0 0 0 {name=p3 lab=IREF}
C {opin.sym} 900 100 0 0 {name=p4 lab=VOUT}
C {iopin.sym} -900 200 0 0 {name=p5 lab=VDD}
C {iopin.sym} -900 300 0 0 {name=p6 lab=VSS}
