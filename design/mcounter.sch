v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: mcounter -- program counter: 4-bit synchronous down counter with PIPELINED control flags (issue #61). Loads M[3:0] when TC (registered, high exactly when Q = 0001), so the period is M clocks (M >= 3). TC/TCN are flop outputs (registered terminal-count pair, TCN = not TC). Each bit toggles on a registered borrow flag (b1..b3 = lower bits of Q are zero), so no flop-to-flop path is deeper than three gates. Self-starting (the flags resynchronise on the first TC). Pinned dff_tg_hv / nand / nor / inv cells.
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
C {dff_tg_hv.sym} 700 0 0 0 {name=XQ1}
C {lab_pin.sym} 660 -20 0 0 {name=l6 lab=D1}
C {lab_pin.sym} 660 20 0 0 {name=l7 lab=CK}
C {lab_pin.sym} 740 0 2 0 {name=l8 lab=q1}
C {lab_pin.sym} 680 -80 0 0 {name=l9 lab=VDD}
C {lab_pin.sym} 720 80 2 0 {name=l10 lab=VSS}
C {dff_tg_hv.sym} 1400 0 0 0 {name=XQ2}
C {lab_pin.sym} 1360 -20 0 0 {name=l11 lab=D2}
C {lab_pin.sym} 1360 20 0 0 {name=l12 lab=CK}
C {lab_pin.sym} 1440 0 2 0 {name=l13 lab=q2}
C {lab_pin.sym} 1380 -80 0 0 {name=l14 lab=VDD}
C {lab_pin.sym} 1420 80 2 0 {name=l15 lab=VSS}
C {dff_tg_hv.sym} 2100 0 0 0 {name=XQ3}
C {lab_pin.sym} 2060 -20 0 0 {name=l16 lab=D3}
C {lab_pin.sym} 2060 20 0 0 {name=l17 lab=CK}
C {lab_pin.sym} 2140 0 2 0 {name=l18 lab=q3}
C {lab_pin.sym} 2080 -80 0 0 {name=l19 lab=VDD}
C {lab_pin.sym} 2120 80 2 0 {name=l20 lab=VSS}
C {dff_tg_hv.sym} 2800 0 0 0 {name=XFT}
C {lab_pin.sym} 2760 -20 0 0 {name=l21 lab=DT}
C {lab_pin.sym} 2760 20 0 0 {name=l22 lab=CK}
C {lab_pin.sym} 2840 0 2 0 {name=l23 lab=TC}
C {lab_pin.sym} 2780 -80 0 0 {name=l24 lab=VDD}
C {lab_pin.sym} 2820 80 2 0 {name=l25 lab=VSS}
C {dff_tg_hv.sym} 3500 0 0 0 {name=XFTN}
C {lab_pin.sym} 3460 -20 0 0 {name=l26 lab=DTN}
C {lab_pin.sym} 3460 20 0 0 {name=l27 lab=CK}
C {lab_pin.sym} 3540 0 2 0 {name=l28 lab=TCN}
C {lab_pin.sym} 3480 -80 0 0 {name=l29 lab=VDD}
C {lab_pin.sym} 3520 80 2 0 {name=l30 lab=VSS}
C {dff_tg_hv.sym} 0 400 0 0 {name=XFB1}
C {lab_pin.sym} -40 380 0 0 {name=l31 lab=DB1}
C {lab_pin.sym} -40 420 0 0 {name=l32 lab=CK}
C {lab_pin.sym} 40 400 2 0 {name=l33 lab=b1}
C {lab_pin.sym} -20 320 0 0 {name=l34 lab=VDD}
C {lab_pin.sym} 20 480 2 0 {name=l35 lab=VSS}
C {dff_tg_hv.sym} 700 400 0 0 {name=XFB2}
C {lab_pin.sym} 660 380 0 0 {name=l36 lab=DB2}
C {lab_pin.sym} 660 420 0 0 {name=l37 lab=CK}
C {lab_pin.sym} 740 400 2 0 {name=l38 lab=b2}
C {lab_pin.sym} 680 320 0 0 {name=l39 lab=VDD}
C {lab_pin.sym} 720 480 2 0 {name=l40 lab=VSS}
C {dff_tg_hv.sym} 1400 400 0 0 {name=XFB3}
C {lab_pin.sym} 1360 380 0 0 {name=l41 lab=DB3}
C {lab_pin.sym} 1360 420 0 0 {name=l42 lab=CK}
C {lab_pin.sym} 1440 400 2 0 {name=l43 lab=b3}
C {lab_pin.sym} 1380 320 0 0 {name=l44 lab=VDD}
C {lab_pin.sym} 1420 480 2 0 {name=l45 lab=VSS}
C {inv_hv.sym} 2100 400 0 0 {name=XIQ0}
C {lab_pin.sym} 2060 400 0 0 {name=l46 lab=q0}
C {lab_pin.sym} 2140 400 2 0 {name=l47 lab=q0n}
C {lab_pin.sym} 2080 360 0 0 {name=l48 lab=VDD}
C {lab_pin.sym} 2120 440 2 0 {name=l49 lab=VSS}
C {inv_hv.sym} 2800 400 0 0 {name=XIQ1}
C {lab_pin.sym} 2760 400 0 0 {name=l50 lab=q1}
C {lab_pin.sym} 2840 400 2 0 {name=l51 lab=q1n}
C {lab_pin.sym} 2780 360 0 0 {name=l52 lab=VDD}
C {lab_pin.sym} 2820 440 2 0 {name=l53 lab=VSS}
C {inv_hv.sym} 3500 400 0 0 {name=XIQ2}
C {lab_pin.sym} 3460 400 0 0 {name=l54 lab=q2}
C {lab_pin.sym} 3540 400 2 0 {name=l55 lab=q2n}
C {lab_pin.sym} 3480 360 0 0 {name=l56 lab=VDD}
C {lab_pin.sym} 3520 440 2 0 {name=l57 lab=VSS}
C {inv_hv.sym} 0 800 0 0 {name=XIQ3}
C {lab_pin.sym} -40 800 0 0 {name=l58 lab=q3}
C {lab_pin.sym} 40 800 2 0 {name=l59 lab=q3n}
C {lab_pin.sym} -20 760 0 0 {name=l60 lab=VDD}
C {lab_pin.sym} 20 840 2 0 {name=l61 lab=VSS}
C {inv_hv.sym} 700 800 0 0 {name=XIB1}
C {lab_pin.sym} 660 800 0 0 {name=l62 lab=b1}
C {lab_pin.sym} 740 800 2 0 {name=l63 lab=b1n}
C {lab_pin.sym} 680 760 0 0 {name=l64 lab=VDD}
C {lab_pin.sym} 720 840 2 0 {name=l65 lab=VSS}
C {inv_hv.sym} 1400 800 0 0 {name=XIB2}
C {lab_pin.sym} 1360 800 0 0 {name=l66 lab=b2}
C {lab_pin.sym} 1440 800 2 0 {name=l67 lab=b2n}
C {lab_pin.sym} 1380 760 0 0 {name=l68 lab=VDD}
C {lab_pin.sym} 1420 840 2 0 {name=l69 lab=VSS}
C {inv_hv.sym} 2100 800 0 0 {name=XIB3}
C {lab_pin.sym} 2060 800 0 0 {name=l70 lab=b3}
C {lab_pin.sym} 2140 800 2 0 {name=l71 lab=b3n}
C {lab_pin.sym} 2080 760 0 0 {name=l72 lab=VDD}
C {lab_pin.sym} 2120 840 2 0 {name=l73 lab=VSS}
C {inv_hv.sym} 2800 800 0 0 {name=XZ1}
C {lab_pin.sym} 2760 800 0 0 {name=l74 lab=M0}
C {lab_pin.sym} 2840 800 2 0 {name=l75 lab=mz1}
C {lab_pin.sym} 2780 760 0 0 {name=l76 lab=VDD}
C {lab_pin.sym} 2820 840 2 0 {name=l77 lab=VSS}
C {nor2_hv.sym} 3500 800 0 0 {name=XZ2}
C {lab_pin.sym} 3460 780 0 0 {name=l78 lab=M0}
C {lab_pin.sym} 3460 820 0 0 {name=l79 lab=M1}
C {lab_pin.sym} 3540 800 2 0 {name=l80 lab=mz2}
C {lab_pin.sym} 3480 720 0 0 {name=l81 lab=VDD}
C {lab_pin.sym} 3520 880 2 0 {name=l82 lab=VSS}
C {nor2_hv.sym} 0 1200 0 0 {name=XZ3A}
C {lab_pin.sym} -40 1180 0 0 {name=l83 lab=M0}
C {lab_pin.sym} -40 1220 0 0 {name=l84 lab=M1}
C {lab_pin.sym} 40 1200 2 0 {name=l85 lab=z01}
C {lab_pin.sym} -20 1120 0 0 {name=l86 lab=VDD}
C {lab_pin.sym} 20 1280 2 0 {name=l87 lab=VSS}
C {inv_hv.sym} 700 1200 0 0 {name=XZ3C}
C {lab_pin.sym} 660 1200 0 0 {name=l88 lab=M2}
C {lab_pin.sym} 740 1200 2 0 {name=l89 lab=M2n}
C {lab_pin.sym} 680 1160 0 0 {name=l90 lab=VDD}
C {lab_pin.sym} 720 1240 2 0 {name=l91 lab=VSS}
C {nand2_hv.sym} 1400 1200 0 0 {name=XZ3B}
C {lab_pin.sym} 1360 1180 0 0 {name=l92 lab=z01}
C {lab_pin.sym} 1360 1220 0 0 {name=l93 lab=M2n}
C {lab_pin.sym} 1440 1200 2 0 {name=l94 lab=mz3n}
C {lab_pin.sym} 1380 1120 0 0 {name=l95 lab=VDD}
C {lab_pin.sym} 1420 1280 2 0 {name=l96 lab=VSS}
C {inv_hv.sym} 2100 1200 0 0 {name=XZ3D}
C {lab_pin.sym} 2060 1200 0 0 {name=l97 lab=mz3n}
C {lab_pin.sym} 2140 1200 2 0 {name=l98 lab=mz3}
C {lab_pin.sym} 2080 1160 0 0 {name=l99 lab=VDD}
C {lab_pin.sym} 2120 1240 2 0 {name=l100 lab=VSS}
C {nand2_hv.sym} 2800 1200 0 0 {name=XL0A}
C {lab_pin.sym} 2760 1180 0 0 {name=l101 lab=q0n}
C {lab_pin.sym} 2760 1220 0 0 {name=l102 lab=TCN}
C {lab_pin.sym} 2840 1200 2 0 {name=l103 lab=l0a}
C {lab_pin.sym} 2780 1120 0 0 {name=l104 lab=VDD}
C {lab_pin.sym} 2820 1280 2 0 {name=l105 lab=VSS}
C {nand2_hv.sym} 3500 1200 0 0 {name=XL0B}
C {lab_pin.sym} 3460 1180 0 0 {name=l106 lab=M0}
C {lab_pin.sym} 3460 1220 0 0 {name=l107 lab=TC}
C {lab_pin.sym} 3540 1200 2 0 {name=l108 lab=l0b}
C {lab_pin.sym} 3480 1120 0 0 {name=l109 lab=VDD}
C {lab_pin.sym} 3520 1280 2 0 {name=l110 lab=VSS}
C {nand2_hv.sym} 0 1600 0 0 {name=XL0Y}
C {lab_pin.sym} -40 1580 0 0 {name=l111 lab=l0a}
C {lab_pin.sym} -40 1620 0 0 {name=l112 lab=l0b}
C {lab_pin.sym} 40 1600 2 0 {name=l113 lab=D0}
C {lab_pin.sym} -20 1520 0 0 {name=l114 lab=VDD}
C {lab_pin.sym} 20 1680 2 0 {name=l115 lab=VSS}
C {nand2_hv.sym} 700 1600 0 0 {name=XA1}
C {lab_pin.sym} 660 1580 0 0 {name=l116 lab=b1}
C {lab_pin.sym} 660 1620 0 0 {name=l117 lab=q1n}
C {lab_pin.sym} 740 1600 2 0 {name=l118 lab=a1}
C {lab_pin.sym} 680 1520 0 0 {name=l119 lab=VDD}
C {lab_pin.sym} 720 1680 2 0 {name=l120 lab=VSS}
C {nand3_hv.sym} 1400 1600 0 0 {name=XB1}
C {lab_pin.sym} 1360 1560 0 0 {name=l121 lab=b1n}
C {lab_pin.sym} 1360 1600 0 0 {name=l122 lab=TCN}
C {lab_pin.sym} 1360 1640 0 0 {name=l123 lab=q1}
C {lab_pin.sym} 1440 1600 2 0 {name=l124 lab=c1}
C {lab_pin.sym} 1380 1480 0 0 {name=l125 lab=VDD}
C {lab_pin.sym} 1420 1720 2 0 {name=l126 lab=VSS}
C {nand2_hv.sym} 2100 1600 0 0 {name=XL1B}
C {lab_pin.sym} 2060 1580 0 0 {name=l127 lab=M1}
C {lab_pin.sym} 2060 1620 0 0 {name=l128 lab=TC}
C {lab_pin.sym} 2140 1600 2 0 {name=l129 lab=l1b}
C {lab_pin.sym} 2080 1520 0 0 {name=l130 lab=VDD}
C {lab_pin.sym} 2120 1680 2 0 {name=l131 lab=VSS}
C {nand3_hv.sym} 2800 1600 0 0 {name=XL1Y}
C {lab_pin.sym} 2760 1560 0 0 {name=l132 lab=a1}
C {lab_pin.sym} 2760 1600 0 0 {name=l133 lab=c1}
C {lab_pin.sym} 2760 1640 0 0 {name=l134 lab=l1b}
C {lab_pin.sym} 2840 1600 2 0 {name=l135 lab=D1}
C {lab_pin.sym} 2780 1480 0 0 {name=l136 lab=VDD}
C {lab_pin.sym} 2820 1720 2 0 {name=l137 lab=VSS}
C {nand2_hv.sym} 3500 1600 0 0 {name=XA2}
C {lab_pin.sym} 3460 1580 0 0 {name=l138 lab=b2}
C {lab_pin.sym} 3460 1620 0 0 {name=l139 lab=q2n}
C {lab_pin.sym} 3540 1600 2 0 {name=l140 lab=a2}
C {lab_pin.sym} 3480 1520 0 0 {name=l141 lab=VDD}
C {lab_pin.sym} 3520 1680 2 0 {name=l142 lab=VSS}
C {nand3_hv.sym} 0 2000 0 0 {name=XB2}
C {lab_pin.sym} -40 1960 0 0 {name=l143 lab=b2n}
C {lab_pin.sym} -40 2000 0 0 {name=l144 lab=TCN}
C {lab_pin.sym} -40 2040 0 0 {name=l145 lab=q2}
C {lab_pin.sym} 40 2000 2 0 {name=l146 lab=c2}
C {lab_pin.sym} -20 1880 0 0 {name=l147 lab=VDD}
C {lab_pin.sym} 20 2120 2 0 {name=l148 lab=VSS}
C {nand2_hv.sym} 700 2000 0 0 {name=XL2B}
C {lab_pin.sym} 660 1980 0 0 {name=l149 lab=M2}
C {lab_pin.sym} 660 2020 0 0 {name=l150 lab=TC}
C {lab_pin.sym} 740 2000 2 0 {name=l151 lab=l2b}
C {lab_pin.sym} 680 1920 0 0 {name=l152 lab=VDD}
C {lab_pin.sym} 720 2080 2 0 {name=l153 lab=VSS}
C {nand3_hv.sym} 1400 2000 0 0 {name=XL2Y}
C {lab_pin.sym} 1360 1960 0 0 {name=l154 lab=a2}
C {lab_pin.sym} 1360 2000 0 0 {name=l155 lab=c2}
C {lab_pin.sym} 1360 2040 0 0 {name=l156 lab=l2b}
C {lab_pin.sym} 1440 2000 2 0 {name=l157 lab=D2}
C {lab_pin.sym} 1380 1880 0 0 {name=l158 lab=VDD}
C {lab_pin.sym} 1420 2120 2 0 {name=l159 lab=VSS}
C {nand2_hv.sym} 2100 2000 0 0 {name=XA3}
C {lab_pin.sym} 2060 1980 0 0 {name=l160 lab=b3}
C {lab_pin.sym} 2060 2020 0 0 {name=l161 lab=q3n}
C {lab_pin.sym} 2140 2000 2 0 {name=l162 lab=a3}
C {lab_pin.sym} 2080 1920 0 0 {name=l163 lab=VDD}
C {lab_pin.sym} 2120 2080 2 0 {name=l164 lab=VSS}
C {nand3_hv.sym} 2800 2000 0 0 {name=XB3}
C {lab_pin.sym} 2760 1960 0 0 {name=l165 lab=b3n}
C {lab_pin.sym} 2760 2000 0 0 {name=l166 lab=TCN}
C {lab_pin.sym} 2760 2040 0 0 {name=l167 lab=q3}
C {lab_pin.sym} 2840 2000 2 0 {name=l168 lab=c3}
C {lab_pin.sym} 2780 1880 0 0 {name=l169 lab=VDD}
C {lab_pin.sym} 2820 2120 2 0 {name=l170 lab=VSS}
C {nand2_hv.sym} 3500 2000 0 0 {name=XL3B}
C {lab_pin.sym} 3460 1980 0 0 {name=l171 lab=M3}
C {lab_pin.sym} 3460 2020 0 0 {name=l172 lab=TC}
C {lab_pin.sym} 3540 2000 2 0 {name=l173 lab=l3b}
C {lab_pin.sym} 3480 1920 0 0 {name=l174 lab=VDD}
C {lab_pin.sym} 3520 2080 2 0 {name=l175 lab=VSS}
C {nand3_hv.sym} 0 2400 0 0 {name=XL3Y}
C {lab_pin.sym} -40 2360 0 0 {name=l176 lab=a3}
C {lab_pin.sym} -40 2400 0 0 {name=l177 lab=c3}
C {lab_pin.sym} -40 2440 0 0 {name=l178 lab=l3b}
C {lab_pin.sym} 40 2400 2 0 {name=l179 lab=D3}
C {lab_pin.sym} -20 2280 0 0 {name=l180 lab=VDD}
C {lab_pin.sym} 20 2520 2 0 {name=l181 lab=VSS}
C {nand2_hv.sym} 700 2400 0 0 {name=XP1A}
C {lab_pin.sym} 660 2380 0 0 {name=l182 lab=TC}
C {lab_pin.sym} 660 2420 0 0 {name=l183 lab=mz1}
C {lab_pin.sym} 740 2400 2 0 {name=l184 lab=p1a}
C {lab_pin.sym} 680 2320 0 0 {name=l185 lab=VDD}
C {lab_pin.sym} 720 2480 2 0 {name=l186 lab=VSS}
C {nand2_hv.sym} 1400 2400 0 0 {name=XP1B}
C {lab_pin.sym} 1360 2380 0 0 {name=l187 lab=TCN}
C {lab_pin.sym} 1360 2420 0 0 {name=l188 lab=q0}
C {lab_pin.sym} 1440 2400 2 0 {name=l189 lab=p1b}
C {lab_pin.sym} 1380 2320 0 0 {name=l190 lab=VDD}
C {lab_pin.sym} 1420 2480 2 0 {name=l191 lab=VSS}
C {nand2_hv.sym} 2100 2400 0 0 {name=XP1Y}
C {lab_pin.sym} 2060 2380 0 0 {name=l192 lab=p1a}
C {lab_pin.sym} 2060 2420 0 0 {name=l193 lab=p1b}
C {lab_pin.sym} 2140 2400 2 0 {name=l194 lab=DB1}
C {lab_pin.sym} 2080 2320 0 0 {name=l195 lab=VDD}
C {lab_pin.sym} 2120 2480 2 0 {name=l196 lab=VSS}
C {nand2_hv.sym} 2800 2400 0 0 {name=XP2A}
C {lab_pin.sym} 2760 2380 0 0 {name=l197 lab=TC}
C {lab_pin.sym} 2760 2420 0 0 {name=l198 lab=mz2}
C {lab_pin.sym} 2840 2400 2 0 {name=l199 lab=p2a}
C {lab_pin.sym} 2780 2320 0 0 {name=l200 lab=VDD}
C {lab_pin.sym} 2820 2480 2 0 {name=l201 lab=VSS}
C {nand3_hv.sym} 3500 2400 0 0 {name=XP2B}
C {lab_pin.sym} 3460 2360 0 0 {name=l202 lab=TCN}
C {lab_pin.sym} 3460 2400 0 0 {name=l203 lab=q0}
C {lab_pin.sym} 3460 2440 0 0 {name=l204 lab=q1n}
C {lab_pin.sym} 3540 2400 2 0 {name=l205 lab=p2b}
C {lab_pin.sym} 3480 2280 0 0 {name=l206 lab=VDD}
C {lab_pin.sym} 3520 2520 2 0 {name=l207 lab=VSS}
C {nand2_hv.sym} 0 2800 0 0 {name=XP2Y}
C {lab_pin.sym} -40 2780 0 0 {name=l208 lab=p2a}
C {lab_pin.sym} -40 2820 0 0 {name=l209 lab=p2b}
C {lab_pin.sym} 40 2800 2 0 {name=l210 lab=DB2}
C {lab_pin.sym} -20 2720 0 0 {name=l211 lab=VDD}
C {lab_pin.sym} 20 2880 2 0 {name=l212 lab=VSS}
C {nor2_hv.sym} 700 2800 0 0 {name=XP3E}
C {lab_pin.sym} 660 2780 0 0 {name=l213 lab=q1}
C {lab_pin.sym} 660 2820 0 0 {name=l214 lab=q2}
C {lab_pin.sym} 740 2800 2 0 {name=l215 lab=e12}
C {lab_pin.sym} 680 2720 0 0 {name=l216 lab=VDD}
C {lab_pin.sym} 720 2880 2 0 {name=l217 lab=VSS}
C {nand2_hv.sym} 1400 2800 0 0 {name=XP3A}
C {lab_pin.sym} 1360 2780 0 0 {name=l218 lab=TC}
C {lab_pin.sym} 1360 2820 0 0 {name=l219 lab=mz3}
C {lab_pin.sym} 1440 2800 2 0 {name=l220 lab=p3a}
C {lab_pin.sym} 1380 2720 0 0 {name=l221 lab=VDD}
C {lab_pin.sym} 1420 2880 2 0 {name=l222 lab=VSS}
C {nand3_hv.sym} 2100 2800 0 0 {name=XP3B}
C {lab_pin.sym} 2060 2760 0 0 {name=l223 lab=TCN}
C {lab_pin.sym} 2060 2800 0 0 {name=l224 lab=q0}
C {lab_pin.sym} 2060 2840 0 0 {name=l225 lab=e12}
C {lab_pin.sym} 2140 2800 2 0 {name=l226 lab=p3b}
C {lab_pin.sym} 2080 2680 0 0 {name=l227 lab=VDD}
C {lab_pin.sym} 2120 2920 2 0 {name=l228 lab=VSS}
C {nand2_hv.sym} 2800 2800 0 0 {name=XP3Y}
C {lab_pin.sym} 2760 2780 0 0 {name=l229 lab=p3a}
C {lab_pin.sym} 2760 2820 0 0 {name=l230 lab=p3b}
C {lab_pin.sym} 2840 2800 2 0 {name=l231 lab=DB3}
C {lab_pin.sym} 2780 2720 0 0 {name=l232 lab=VDD}
C {lab_pin.sym} 2820 2880 2 0 {name=l233 lab=VSS}
C {nor2_hv.sym} 3500 2800 0 0 {name=XT1}
C {lab_pin.sym} 3460 2780 0 0 {name=l234 lab=q3}
C {lab_pin.sym} 3460 2820 0 0 {name=l235 lab=q2}
C {lab_pin.sym} 3540 2800 2 0 {name=l236 lab=f32}
C {lab_pin.sym} 3480 2720 0 0 {name=l237 lab=VDD}
C {lab_pin.sym} 3520 2880 2 0 {name=l238 lab=VSS}
C {nor2_hv.sym} 0 3200 0 0 {name=XT2}
C {lab_pin.sym} -40 3180 0 0 {name=l239 lab=q0}
C {lab_pin.sym} -40 3220 0 0 {name=l240 lab=q1n}
C {lab_pin.sym} 40 3200 2 0 {name=l241 lab=g10}
C {lab_pin.sym} -20 3120 0 0 {name=l242 lab=VDD}
C {lab_pin.sym} 20 3280 2 0 {name=l243 lab=VSS}
C {nand2_hv.sym} 700 3200 0 0 {name=XT3}
C {lab_pin.sym} 660 3180 0 0 {name=l244 lab=f32}
C {lab_pin.sym} 660 3220 0 0 {name=l245 lab=g10}
C {lab_pin.sym} 740 3200 2 0 {name=l246 lab=DTN}
C {lab_pin.sym} 680 3120 0 0 {name=l247 lab=VDD}
C {lab_pin.sym} 720 3280 2 0 {name=l248 lab=VSS}
C {inv_hv.sym} 1400 3200 0 0 {name=XT4}
C {lab_pin.sym} 1360 3200 0 0 {name=l249 lab=DTN}
C {lab_pin.sym} 1440 3200 2 0 {name=l250 lab=DT}
C {lab_pin.sym} 1380 3160 0 0 {name=l251 lab=VDD}
C {lab_pin.sym} 1420 3240 2 0 {name=l252 lab=VSS}
C {ipin.sym} -900 -200 0 0 {name=p1 lab=CK}
C {ipin.sym} -900 -100 0 0 {name=p2 lab=M0}
C {ipin.sym} -900 0 0 0 {name=p3 lab=M1}
C {ipin.sym} -900 100 0 0 {name=p4 lab=M2}
C {ipin.sym} -900 200 0 0 {name=p5 lab=M3}
C {opin.sym} -900 300 0 0 {name=p6 lab=TC}
C {opin.sym} -900 400 0 0 {name=p7 lab=TCN}
C {iopin.sym} -900 500 0 0 {name=p8 lab=VDD}
C {iopin.sym} -900 600 0 0 {name=p9 lab=VSS}
