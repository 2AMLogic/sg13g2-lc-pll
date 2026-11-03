v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: mcounter -- program counter: 4-bit synchronous down counter, loads M[3:0] when Q = 0001 (terminal count TC), so the period is M clocks. TCN = not TC. Self-starting (any state reaches Q = 0001 within 16 clocks). Pinned dff_tg_hv / xor2_hv / nand / nor / inv cells.
}
G {}
K {}
V {}
S {}
E {}
C {dff_tg_hv.sym} 0 0 0 0 {name=XQ0}
C {lab_pin.sym} -40 -20 0 0 {name=l1 lab=D0}
C {lab_pin.sym} -40 20 0 0 {name=l2 lab=CK}
C {lab_pin.sym} 40 0 2 0 {name=l3 lab=q0}
C {lab_pin.sym} -20 -80 0 0 {name=l4 lab=VDD}
C {lab_pin.sym} 20 80 2 0 {name=l5 lab=VSS}
C {dff_tg_hv.sym} 600 0 0 0 {name=XQ1}
C {lab_pin.sym} 560 -20 0 0 {name=l6 lab=D1}
C {lab_pin.sym} 560 20 0 0 {name=l7 lab=CK}
C {lab_pin.sym} 640 0 2 0 {name=l8 lab=q1}
C {lab_pin.sym} 580 -80 0 0 {name=l9 lab=VDD}
C {lab_pin.sym} 620 80 2 0 {name=l10 lab=VSS}
C {dff_tg_hv.sym} 1200 0 0 0 {name=XQ2}
C {lab_pin.sym} 1160 -20 0 0 {name=l11 lab=D2}
C {lab_pin.sym} 1160 20 0 0 {name=l12 lab=CK}
C {lab_pin.sym} 1240 0 2 0 {name=l13 lab=q2}
C {lab_pin.sym} 1180 -80 0 0 {name=l14 lab=VDD}
C {lab_pin.sym} 1220 80 2 0 {name=l15 lab=VSS}
C {dff_tg_hv.sym} 1800 0 0 0 {name=XQ3}
C {lab_pin.sym} 1760 -20 0 0 {name=l16 lab=D3}
C {lab_pin.sym} 1760 20 0 0 {name=l17 lab=CK}
C {lab_pin.sym} 1840 0 2 0 {name=l18 lab=q3}
C {lab_pin.sym} 1780 -80 0 0 {name=l19 lab=VDD}
C {lab_pin.sym} 1820 80 2 0 {name=l20 lab=VSS}
C {nor2_hv.sym} 2400 0 0 0 {name=XTC1}
C {lab_pin.sym} 2360 -20 0 0 {name=l21 lab=q1}
C {lab_pin.sym} 2360 20 0 0 {name=l22 lab=q2}
C {lab_pin.sym} 2440 0 2 0 {name=l23 lab=n12}
C {lab_pin.sym} 2380 -80 0 0 {name=l24 lab=VDD}
C {lab_pin.sym} 2420 80 2 0 {name=l25 lab=VSS}
C {inv_hv.sym} 3000 0 0 0 {name=XTC2}
C {lab_pin.sym} 2960 0 0 0 {name=l26 lab=q3}
C {lab_pin.sym} 3040 0 2 0 {name=l27 lab=q3b}
C {lab_pin.sym} 2980 -40 0 0 {name=l28 lab=VDD}
C {lab_pin.sym} 3020 40 2 0 {name=l29 lab=VSS}
C {nand3_hv.sym} 0 600 0 0 {name=XTC3}
C {lab_pin.sym} -40 560 0 0 {name=l30 lab=q0}
C {lab_pin.sym} -40 600 0 0 {name=l31 lab=n12}
C {lab_pin.sym} -40 640 0 0 {name=l32 lab=q3b}
C {lab_pin.sym} 40 600 2 0 {name=l33 lab=TCN}
C {lab_pin.sym} -20 480 0 0 {name=l34 lab=VDD}
C {lab_pin.sym} 20 720 2 0 {name=l35 lab=VSS}
C {inv_hv.sym} 600 600 0 0 {name=XTC4}
C {lab_pin.sym} 560 600 0 0 {name=l36 lab=TCN}
C {lab_pin.sym} 640 600 2 0 {name=l37 lab=TC}
C {lab_pin.sym} 580 560 0 0 {name=l38 lab=VDD}
C {lab_pin.sym} 620 640 2 0 {name=l39 lab=VSS}
C {inv_hv.sym} 1200 600 0 0 {name=XD0}
C {lab_pin.sym} 1160 600 0 0 {name=l40 lab=q0}
C {lab_pin.sym} 1240 600 2 0 {name=l41 lab=dec0}
C {lab_pin.sym} 1180 560 0 0 {name=l42 lab=VDD}
C {lab_pin.sym} 1220 640 2 0 {name=l43 lab=VSS}
C {xor2_hv.sym} 1800 600 0 0 {name=XD1}
C {lab_pin.sym} 1760 580 0 0 {name=l44 lab=q1}
C {lab_pin.sym} 1760 620 0 0 {name=l45 lab=dec0}
C {lab_pin.sym} 1840 600 2 0 {name=l46 lab=dec1}
C {lab_pin.sym} 1780 520 0 0 {name=l47 lab=VDD}
C {lab_pin.sym} 1820 680 2 0 {name=l48 lab=VSS}
C {nor2_hv.sym} 2400 600 0 0 {name=XD2A}
C {lab_pin.sym} 2360 580 0 0 {name=l49 lab=q1}
C {lab_pin.sym} 2360 620 0 0 {name=l50 lab=q0}
C {lab_pin.sym} 2440 600 2 0 {name=l51 lab=n10}
C {lab_pin.sym} 2380 520 0 0 {name=l52 lab=VDD}
C {lab_pin.sym} 2420 680 2 0 {name=l53 lab=VSS}
C {xor2_hv.sym} 3000 600 0 0 {name=XD2}
C {lab_pin.sym} 2960 580 0 0 {name=l54 lab=q2}
C {lab_pin.sym} 2960 620 0 0 {name=l55 lab=n10}
C {lab_pin.sym} 3040 600 2 0 {name=l56 lab=dec2}
C {lab_pin.sym} 2980 520 0 0 {name=l57 lab=VDD}
C {lab_pin.sym} 3020 680 2 0 {name=l58 lab=VSS}
C {inv_hv.sym} 0 1200 0 0 {name=XD3A}
C {lab_pin.sym} -40 1200 0 0 {name=l59 lab=n10}
C {lab_pin.sym} 40 1200 2 0 {name=l60 lab=n10b}
C {lab_pin.sym} -20 1160 0 0 {name=l61 lab=VDD}
C {lab_pin.sym} 20 1240 2 0 {name=l62 lab=VSS}
C {nor2_hv.sym} 600 1200 0 0 {name=XD3B}
C {lab_pin.sym} 560 1180 0 0 {name=l63 lab=q2}
C {lab_pin.sym} 560 1220 0 0 {name=l64 lab=n10b}
C {lab_pin.sym} 640 1200 2 0 {name=l65 lab=n210}
C {lab_pin.sym} 580 1120 0 0 {name=l66 lab=VDD}
C {lab_pin.sym} 620 1280 2 0 {name=l67 lab=VSS}
C {xor2_hv.sym} 1200 1200 0 0 {name=XD3}
C {lab_pin.sym} 1160 1180 0 0 {name=l68 lab=q3}
C {lab_pin.sym} 1160 1220 0 0 {name=l69 lab=n210}
C {lab_pin.sym} 1240 1200 2 0 {name=l70 lab=dec3}
C {lab_pin.sym} 1180 1120 0 0 {name=l71 lab=VDD}
C {lab_pin.sym} 1220 1280 2 0 {name=l72 lab=VSS}
C {nand2_hv.sym} 1800 1200 0 0 {name=XNL0A}
C {lab_pin.sym} 1760 1180 0 0 {name=l73 lab=dec0}
C {lab_pin.sym} 1760 1220 0 0 {name=l74 lab=TCN}
C {lab_pin.sym} 1840 1200 2 0 {name=l75 lab=L0_na}
C {lab_pin.sym} 1780 1120 0 0 {name=l76 lab=VDD}
C {lab_pin.sym} 1820 1280 2 0 {name=l77 lab=VSS}
C {nand2_hv.sym} 2400 1200 0 0 {name=XNL0B}
C {lab_pin.sym} 2360 1180 0 0 {name=l78 lab=M0}
C {lab_pin.sym} 2360 1220 0 0 {name=l79 lab=TC}
C {lab_pin.sym} 2440 1200 2 0 {name=l80 lab=L0_nb}
C {lab_pin.sym} 2380 1120 0 0 {name=l81 lab=VDD}
C {lab_pin.sym} 2420 1280 2 0 {name=l82 lab=VSS}
C {nand2_hv.sym} 3000 1200 0 0 {name=XNL0Y}
C {lab_pin.sym} 2960 1180 0 0 {name=l83 lab=L0_na}
C {lab_pin.sym} 2960 1220 0 0 {name=l84 lab=L0_nb}
C {lab_pin.sym} 3040 1200 2 0 {name=l85 lab=D0}
C {lab_pin.sym} 2980 1120 0 0 {name=l86 lab=VDD}
C {lab_pin.sym} 3020 1280 2 0 {name=l87 lab=VSS}
C {nand2_hv.sym} 0 1800 0 0 {name=XNL1A}
C {lab_pin.sym} -40 1780 0 0 {name=l88 lab=dec1}
C {lab_pin.sym} -40 1820 0 0 {name=l89 lab=TCN}
C {lab_pin.sym} 40 1800 2 0 {name=l90 lab=L1_na}
C {lab_pin.sym} -20 1720 0 0 {name=l91 lab=VDD}
C {lab_pin.sym} 20 1880 2 0 {name=l92 lab=VSS}
C {nand2_hv.sym} 600 1800 0 0 {name=XNL1B}
C {lab_pin.sym} 560 1780 0 0 {name=l93 lab=M1}
C {lab_pin.sym} 560 1820 0 0 {name=l94 lab=TC}
C {lab_pin.sym} 640 1800 2 0 {name=l95 lab=L1_nb}
C {lab_pin.sym} 580 1720 0 0 {name=l96 lab=VDD}
C {lab_pin.sym} 620 1880 2 0 {name=l97 lab=VSS}
C {nand2_hv.sym} 1200 1800 0 0 {name=XNL1Y}
C {lab_pin.sym} 1160 1780 0 0 {name=l98 lab=L1_na}
C {lab_pin.sym} 1160 1820 0 0 {name=l99 lab=L1_nb}
C {lab_pin.sym} 1240 1800 2 0 {name=l100 lab=D1}
C {lab_pin.sym} 1180 1720 0 0 {name=l101 lab=VDD}
C {lab_pin.sym} 1220 1880 2 0 {name=l102 lab=VSS}
C {nand2_hv.sym} 1800 1800 0 0 {name=XNL2A}
C {lab_pin.sym} 1760 1780 0 0 {name=l103 lab=dec2}
C {lab_pin.sym} 1760 1820 0 0 {name=l104 lab=TCN}
C {lab_pin.sym} 1840 1800 2 0 {name=l105 lab=L2_na}
C {lab_pin.sym} 1780 1720 0 0 {name=l106 lab=VDD}
C {lab_pin.sym} 1820 1880 2 0 {name=l107 lab=VSS}
C {nand2_hv.sym} 2400 1800 0 0 {name=XNL2B}
C {lab_pin.sym} 2360 1780 0 0 {name=l108 lab=M2}
C {lab_pin.sym} 2360 1820 0 0 {name=l109 lab=TC}
C {lab_pin.sym} 2440 1800 2 0 {name=l110 lab=L2_nb}
C {lab_pin.sym} 2380 1720 0 0 {name=l111 lab=VDD}
C {lab_pin.sym} 2420 1880 2 0 {name=l112 lab=VSS}
C {nand2_hv.sym} 3000 1800 0 0 {name=XNL2Y}
C {lab_pin.sym} 2960 1780 0 0 {name=l113 lab=L2_na}
C {lab_pin.sym} 2960 1820 0 0 {name=l114 lab=L2_nb}
C {lab_pin.sym} 3040 1800 2 0 {name=l115 lab=D2}
C {lab_pin.sym} 2980 1720 0 0 {name=l116 lab=VDD}
C {lab_pin.sym} 3020 1880 2 0 {name=l117 lab=VSS}
C {nand2_hv.sym} 0 2400 0 0 {name=XNL3A}
C {lab_pin.sym} -40 2380 0 0 {name=l118 lab=dec3}
C {lab_pin.sym} -40 2420 0 0 {name=l119 lab=TCN}
C {lab_pin.sym} 40 2400 2 0 {name=l120 lab=L3_na}
C {lab_pin.sym} -20 2320 0 0 {name=l121 lab=VDD}
C {lab_pin.sym} 20 2480 2 0 {name=l122 lab=VSS}
C {nand2_hv.sym} 600 2400 0 0 {name=XNL3B}
C {lab_pin.sym} 560 2380 0 0 {name=l123 lab=M3}
C {lab_pin.sym} 560 2420 0 0 {name=l124 lab=TC}
C {lab_pin.sym} 640 2400 2 0 {name=l125 lab=L3_nb}
C {lab_pin.sym} 580 2320 0 0 {name=l126 lab=VDD}
C {lab_pin.sym} 620 2480 2 0 {name=l127 lab=VSS}
C {nand2_hv.sym} 1200 2400 0 0 {name=XNL3Y}
C {lab_pin.sym} 1160 2380 0 0 {name=l128 lab=L3_na}
C {lab_pin.sym} 1160 2420 0 0 {name=l129 lab=L3_nb}
C {lab_pin.sym} 1240 2400 2 0 {name=l130 lab=D3}
C {lab_pin.sym} 1180 2320 0 0 {name=l131 lab=VDD}
C {lab_pin.sym} 1220 2480 2 0 {name=l132 lab=VSS}
C {ipin.sym} -900 -200 0 0 {name=p1 lab=CK}
C {ipin.sym} -900 -100 0 0 {name=p2 lab=M0}
C {ipin.sym} -900 0 0 0 {name=p3 lab=M1}
C {ipin.sym} -900 100 0 0 {name=p4 lab=M2}
C {ipin.sym} -900 200 0 0 {name=p5 lab=M3}
C {opin.sym} -900 300 0 0 {name=p6 lab=TC}
C {opin.sym} -900 400 0 0 {name=p7 lab=TCN}
C {iopin.sym} -900 500 0 0 {name=p8 lab=VDD}
C {iopin.sym} -900 600 0 0 {name=p9 lab=VSS}
