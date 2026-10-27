v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: cml_div23 -- divide-by-2/3 cell: D1 = NOR(Q1,Q2), D2 = Q1 AND M; M high swallows one input cycle (3), M low gives 2
}
G {}
K {}
V {}
S {}
E {}
C {cml_ef.sym} 400 0 0 0 {name=XCK}
C {lab_pin.sym} 360 -40 0 0 {name=l1 lab=INP}
C {lab_pin.sym} 360 0 0 0 {name=l2 lab=INN}
C {lab_pin.sym} 360 40 0 0 {name=l3 lab=IB}
C {lab_pin.sym} 440 -20 2 0 {name=l4 lab=CKP}
C {lab_pin.sym} 440 20 2 0 {name=l5 lab=CKN}
C {lab_pin.sym} 400 -120 2 0 {name=l6 lab=VDD}
C {lab_pin.sym} 400 120 2 0 {name=l7 lab=VSS}
C {cml_ef.sym} 800 0 0 0 {name=XQ1L}
C {lab_pin.sym} 760 -40 0 0 {name=l8 lab=Q1}
C {lab_pin.sym} 760 0 0 0 {name=l9 lab=Q1B}
C {lab_pin.sym} 760 40 0 0 {name=l10 lab=IB}
C {lab_pin.sym} 840 -20 2 0 {name=l11 lab=Q1L}
C {lab_pin.sym} 840 20 2 0 {name=l12 lab=Q1LB}
C {lab_pin.sym} 800 -120 2 0 {name=l13 lab=VDD}
C {lab_pin.sym} 800 120 2 0 {name=l14 lab=VSS}
C {cml_and2.sym} 1200 0 0 0 {name=XG1}
C {lab_pin.sym} 1160 -80 0 0 {name=l15 lab=Q2B}
C {lab_pin.sym} 1160 -40 0 0 {name=l16 lab=Q2}
C {lab_pin.sym} 1160 0 0 0 {name=l17 lab=Q1LB}
C {lab_pin.sym} 1160 40 0 0 {name=l18 lab=Q1L}
C {lab_pin.sym} 1160 80 0 0 {name=l19 lab=IB}
C {lab_pin.sym} 1240 -20 2 0 {name=l20 lab=D1}
C {lab_pin.sym} 1240 20 2 0 {name=l21 lab=D1B}
C {lab_pin.sym} 1200 -160 2 0 {name=l22 lab=VDD}
C {lab_pin.sym} 1200 160 2 0 {name=l23 lab=VSS}
C {cml_and2.sym} 1600 0 0 0 {name=XG2}
C {lab_pin.sym} 1560 -80 0 0 {name=l24 lab=M}
C {lab_pin.sym} 1560 -40 0 0 {name=l25 lab=MB}
C {lab_pin.sym} 1560 0 0 0 {name=l26 lab=Q1L}
C {lab_pin.sym} 1560 40 0 0 {name=l27 lab=Q1LB}
C {lab_pin.sym} 1560 80 0 0 {name=l28 lab=IB}
C {lab_pin.sym} 1640 -20 2 0 {name=l29 lab=D2}
C {lab_pin.sym} 1640 20 2 0 {name=l30 lab=D2B}
C {lab_pin.sym} 1600 -160 2 0 {name=l31 lab=VDD}
C {lab_pin.sym} 1600 160 2 0 {name=l32 lab=VSS}
C {cml_dff.sym} 2000 0 0 0 {name=XF1}
C {lab_pin.sym} 1960 -80 0 0 {name=l33 lab=D1}
C {lab_pin.sym} 1960 -40 0 0 {name=l34 lab=D1B}
C {lab_pin.sym} 1960 0 0 0 {name=l35 lab=CKP}
C {lab_pin.sym} 1960 40 0 0 {name=l36 lab=CKN}
C {lab_pin.sym} 1960 80 0 0 {name=l37 lab=IB}
C {lab_pin.sym} 2040 -20 2 0 {name=l38 lab=Q1}
C {lab_pin.sym} 2040 20 2 0 {name=l39 lab=Q1B}
C {lab_pin.sym} 2000 -160 2 0 {name=l40 lab=VDD}
C {lab_pin.sym} 2000 160 2 0 {name=l41 lab=VSS}
C {cml_dff.sym} 2400 0 0 0 {name=XF2}
C {lab_pin.sym} 2360 -80 0 0 {name=l42 lab=D2}
C {lab_pin.sym} 2360 -40 0 0 {name=l43 lab=D2B}
C {lab_pin.sym} 2360 0 0 0 {name=l44 lab=CKP}
C {lab_pin.sym} 2360 40 0 0 {name=l45 lab=CKN}
C {lab_pin.sym} 2360 80 0 0 {name=l46 lab=IB}
C {lab_pin.sym} 2440 -20 2 0 {name=l47 lab=Q2}
C {lab_pin.sym} 2440 20 2 0 {name=l48 lab=Q2B}
C {lab_pin.sym} 2400 -160 2 0 {name=l49 lab=VDD}
C {lab_pin.sym} 2400 160 2 0 {name=l50 lab=VSS}
C {ipin.sym} -400 0 0 0 {name=p1 lab=INP}
C {ipin.sym} -400 100 0 0 {name=p2 lab=INN}
C {ipin.sym} -400 200 0 0 {name=p3 lab=M}
C {ipin.sym} -400 300 0 0 {name=p4 lab=MB}
C {ipin.sym} -400 400 0 0 {name=p5 lab=IB}
C {opin.sym} 1400 0 0 0 {name=p6 lab=Q1}
C {opin.sym} 1400 100 0 0 {name=p7 lab=Q1B}
C {iopin.sym} -400 -300 0 0 {name=p8 lab=VDD}
C {iopin.sym} -400 -400 0 0 {name=p9 lab=VSS}
