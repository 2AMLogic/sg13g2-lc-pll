v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: cp_bias -- charge-pump bias: IREF -> IBP / ICN / ICP
IREF is the reference current sunk from VDD by the caller (I_cp = K*IREF, K = leg ratio 9.5 here);
the net IREF is also the gate bias of every NMOS mirror device (diode XBN1). Every other bias
branch carries the same unit current. High-swing cascode bias per polarity: the cascode-bias diode
(XBNC / XBPC) is narrower than the leg cascode so the mirror device keeps Vds above Vdsat.
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
C {sg13g2_pr/sg13_hv_nmos.sym} 0 0 0 0 {name=BN1 model=sg13_hv_nmos w=4u l=1u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} -20 0 0 0 {name=l1 lab=IREF}
C {lab_pin.sym} 20 -30 2 0 {name=l2 lab=IREF}
C {lab_pin.sym} 20 30 2 0 {name=l3 lab=VSS}
C {lab_pin.sym} 20 0 2 0 {name=l4 lab=VSS}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 0 0 0 {name=BN2 model=sg13_hv_nmos w=4u l=1u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} 280 0 0 0 {name=l5 lab=IREF}
C {lab_pin.sym} 320 -30 2 0 {name=l6 lab=IBP}
C {lab_pin.sym} 320 30 2 0 {name=l7 lab=VSS}
C {lab_pin.sym} 320 0 2 0 {name=l8 lab=VSS}
C {sg13g2_pr/sg13_hv_pmos.sym} 600 0 0 0 {name=BP1 model=sg13_hv_pmos w=4u l=1u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} 580 0 0 0 {name=l9 lab=IBP}
C {lab_pin.sym} 620 -30 2 0 {name=l10 lab=VDD}
C {lab_pin.sym} 620 30 2 0 {name=l11 lab=IBP}
C {lab_pin.sym} 620 0 2 0 {name=l12 lab=VDD}
C {sg13g2_pr/sg13_hv_pmos.sym} 0 300 0 0 {name=BPS model=sg13_hv_pmos w=4u l=1u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} -20 300 0 0 {name=l13 lab=IBP}
C {lab_pin.sym} 20 270 2 0 {name=l14 lab=VDD}
C {lab_pin.sym} 20 330 2 0 {name=l15 lab=ICN}
C {lab_pin.sym} 20 300 2 0 {name=l16 lab=VDD}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 300 0 0 {name=BNC model=sg13_hv_nmos w=2u l=1u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} 280 300 0 0 {name=l17 lab=ICN}
C {lab_pin.sym} 320 270 2 0 {name=l18 lab=ICN}
C {lab_pin.sym} 320 330 2 0 {name=l19 lab=nx}
C {lab_pin.sym} 320 300 2 0 {name=l20 lab=VSS}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 300 0 0 {name=BNA model=sg13_hv_nmos w=4u l=1u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} 580 300 0 0 {name=l21 lab=IREF}
C {lab_pin.sym} 620 270 2 0 {name=l22 lab=nx}
C {lab_pin.sym} 620 330 2 0 {name=l23 lab=VSS}
C {lab_pin.sym} 620 300 2 0 {name=l24 lab=VSS}
C {sg13g2_pr/sg13_hv_pmos.sym} 0 600 0 0 {name=BPA model=sg13_hv_pmos w=4u l=1u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} -20 600 0 0 {name=l25 lab=IBP}
C {lab_pin.sym} 20 570 2 0 {name=l26 lab=VDD}
C {lab_pin.sym} 20 630 2 0 {name=l27 lab=px}
C {lab_pin.sym} 20 600 2 0 {name=l28 lab=VDD}
C {sg13g2_pr/sg13_hv_pmos.sym} 300 600 0 0 {name=BPC model=sg13_hv_pmos w=3u l=1u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} 280 600 0 0 {name=l29 lab=ICP}
C {lab_pin.sym} 320 570 2 0 {name=l30 lab=px}
C {lab_pin.sym} 320 630 2 0 {name=l31 lab=ICP}
C {lab_pin.sym} 320 600 2 0 {name=l32 lab=VDD}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 600 0 0 {name=BNS model=sg13_hv_nmos w=4u l=1u ng=1 m=1 spiceprefix=X}
C {lab_pin.sym} 580 600 0 0 {name=l33 lab=IREF}
C {lab_pin.sym} 620 570 2 0 {name=l34 lab=ICP}
C {lab_pin.sym} 620 630 2 0 {name=l35 lab=VSS}
C {lab_pin.sym} 620 600 2 0 {name=l36 lab=VSS}
C {ipin.sym} -900 -200 0 0 {name=p1 lab=IREF}
C {opin.sym} 900 -100 0 0 {name=p2 lab=IBP}
C {opin.sym} 900 0 0 0 {name=p3 lab=ICN}
C {opin.sym} 900 100 0 0 {name=p4 lab=ICP}
C {iopin.sym} -900 200 0 0 {name=p5 lab=VDD}
C {iopin.sym} -900 300 0 0 {name=p6 lab=VSS}
