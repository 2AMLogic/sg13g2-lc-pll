v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: div45_dm -- dual-modulus divide-by-4/5: 2/3 cell, then divide-by-2 whose output gates the swallow (M = MC AND OUT); MC high gives 5, low gives 4
}
G {}
K {}
V {}
S {}
E {}
C {mc_conv.sym} 400 0 0 0 {name=XMC}
C {lab_pin.sym} 360 -20 0 0 {name=l1 lab=MC}
C {lab_pin.sym} 360 20 0 0 {name=l2 lab=IB}
C {lab_pin.sym} 440 -20 2 0 {name=l3 lab=MCP}
C {lab_pin.sym} 440 20 2 0 {name=l4 lab=MCN}
C {lab_pin.sym} 400 -100 2 0 {name=l5 lab=VDD}
C {lab_pin.sym} 400 100 2 0 {name=l6 lab=VSS}
C {cml_ef.sym} 800 0 0 0 {name=XMCL}
C {lab_pin.sym} 760 -40 0 0 {name=l7 lab=MCP}
C {lab_pin.sym} 760 0 0 0 {name=l8 lab=MCN}
C {lab_pin.sym} 760 40 0 0 {name=l9 lab=IB}
C {lab_pin.sym} 840 -20 2 0 {name=l10 lab=MCL}
C {lab_pin.sym} 840 20 2 0 {name=l11 lab=MCLB}
C {lab_pin.sym} 800 -120 2 0 {name=l12 lab=VDD}
C {lab_pin.sym} 800 120 2 0 {name=l13 lab=VSS}
C {cml_and2.sym} 1200 0 0 0 {name=XGM}
C {lab_pin.sym} 1160 -80 0 0 {name=l14 lab=OUTP}
C {lab_pin.sym} 1160 -40 0 0 {name=l15 lab=OUTN}
C {lab_pin.sym} 1160 0 0 0 {name=l16 lab=MCL}
C {lab_pin.sym} 1160 40 0 0 {name=l17 lab=MCLB}
C {lab_pin.sym} 1160 80 0 0 {name=l18 lab=IB}
C {lab_pin.sym} 1240 -20 2 0 {name=l19 lab=M}
C {lab_pin.sym} 1240 20 2 0 {name=l20 lab=MB}
C {lab_pin.sym} 1200 -160 2 0 {name=l21 lab=VDD}
C {lab_pin.sym} 1200 160 2 0 {name=l22 lab=VSS}
C {cml_div23.sym} 1600 0 0 0 {name=XC23}
C {lab_pin.sym} 1560 -80 0 0 {name=l23 lab=INP}
C {lab_pin.sym} 1560 -40 0 0 {name=l24 lab=INN}
C {lab_pin.sym} 1560 0 0 0 {name=l25 lab=M}
C {lab_pin.sym} 1560 40 0 0 {name=l26 lab=MB}
C {lab_pin.sym} 1560 80 0 0 {name=l27 lab=IB}
C {lab_pin.sym} 1640 -20 2 0 {name=l28 lab=C1}
C {lab_pin.sym} 1640 20 2 0 {name=l29 lab=C1B}
C {lab_pin.sym} 1600 -160 2 0 {name=l30 lab=VDD}
C {lab_pin.sym} 1600 160 2 0 {name=l31 lab=VSS}
C {div2_cml_ls.sym} 2000 0 0 0 {name=XT}
C {lab_pin.sym} 1960 -40 0 0 {name=l32 lab=C1}
C {lab_pin.sym} 1960 0 0 0 {name=l33 lab=C1B}
C {lab_pin.sym} 1960 40 0 0 {name=l34 lab=IB}
C {lab_pin.sym} 2040 -20 2 0 {name=l35 lab=OUTP}
C {lab_pin.sym} 2040 20 2 0 {name=l36 lab=OUTN}
C {lab_pin.sym} 2000 -120 2 0 {name=l37 lab=VDD}
C {lab_pin.sym} 2000 120 2 0 {name=l38 lab=VSS}
C {ipin.sym} -400 0 0 0 {name=p1 lab=INP}
C {ipin.sym} -400 100 0 0 {name=p2 lab=INN}
C {ipin.sym} -400 200 0 0 {name=p3 lab=MC}
C {ipin.sym} -400 300 0 0 {name=p4 lab=IB}
C {opin.sym} 1400 0 0 0 {name=p5 lab=OUTP}
C {opin.sym} 1400 100 0 0 {name=p6 lab=OUTN}
C {iopin.sym} -400 -300 0 0 {name=p7 lab=VDD}
C {iopin.sym} -400 -400 0 0 {name=p8 lab=VSS}
