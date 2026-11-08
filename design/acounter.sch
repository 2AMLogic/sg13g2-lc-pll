v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: acounter -- swallow counter (state bits s0, s1, s2; SPICE names are case-insensitive, so they must not be a0, a1, a2): 3-bit down counter that holds at 0, loads A[2:0] together with the program counter (TC). MC = (count != 0), a REGISTERED flop output (issue #61): the prescaler divides by 9 in the /2/3 stage (total /9) for A reference cycles after each load, then by 8. N = 9 A + 8 (M - A) = 8 M + A, A in [0, 7] (DR-005, P = 8/9); needs M >= A. Next state (TC low) is a saturating decrement, three gates deep: D0 = (s1|s2)&!s0, D1 = s1&s0 | s2&!s1&!s0, D2 = s2&(s1|s0); next MC = s1|s2 (TC low) or A != 0 (TC high).
}
G {}
K {}
V {}
S {}
E {}
C {dff_tg_hv.sym} 0 0 0 0 {name=XQ0}
C {lab_pin.sym} -40 -20 0 0 {name=l1 lab=D0}
C {lab_pin.sym} -40 20 0 0 {name=l2 lab=CK}
C {lab_pin.sym} 40 0 2 0 {name=l3 lab=s0}
C {lab_pin.sym} -20 -80 0 0 {name=l4 lab=VDD}
C {lab_pin.sym} 20 80 2 0 {name=l5 lab=VSS}
C {dff_tg_hv.sym} 700 0 0 0 {name=XQ1}
C {lab_pin.sym} 660 -20 0 0 {name=l6 lab=D1}
C {lab_pin.sym} 660 20 0 0 {name=l7 lab=CK}
C {lab_pin.sym} 740 0 2 0 {name=l8 lab=s1}
C {lab_pin.sym} 680 -80 0 0 {name=l9 lab=VDD}
C {lab_pin.sym} 720 80 2 0 {name=l10 lab=VSS}
C {dff_tg_hv.sym} 1400 0 0 0 {name=XQ2}
C {lab_pin.sym} 1360 -20 0 0 {name=l11 lab=D2}
C {lab_pin.sym} 1360 20 0 0 {name=l12 lab=CK}
C {lab_pin.sym} 1440 0 2 0 {name=l13 lab=s2}
C {lab_pin.sym} 1380 -80 0 0 {name=l14 lab=VDD}
C {lab_pin.sym} 1420 80 2 0 {name=l15 lab=VSS}
C {dff_tg_hv.sym} 2100 0 0 0 {name=XQM}
C {lab_pin.sym} 2060 -20 0 0 {name=l16 lab=DM}
C {lab_pin.sym} 2060 20 0 0 {name=l17 lab=CK}
C {lab_pin.sym} 2140 0 2 0 {name=l18 lab=MC}
C {lab_pin.sym} 2080 -80 0 0 {name=l19 lab=VDD}
C {lab_pin.sym} 2120 80 2 0 {name=l20 lab=VSS}
C {inv_hv.sym} 2800 0 0 0 {name=XS0}
C {lab_pin.sym} 2760 0 0 0 {name=l21 lab=s0}
C {lab_pin.sym} 2840 0 2 0 {name=l22 lab=s0n}
C {lab_pin.sym} 2780 -40 0 0 {name=l23 lab=VDD}
C {lab_pin.sym} 2820 40 2 0 {name=l24 lab=VSS}
C {inv_hv.sym} 3500 0 0 0 {name=XNA0}
C {lab_pin.sym} 3460 0 0 0 {name=l25 lab=A0}
C {lab_pin.sym} 3540 0 2 0 {name=l26 lab=A0n}
C {lab_pin.sym} 3480 -40 0 0 {name=l27 lab=VDD}
C {lab_pin.sym} 3520 40 2 0 {name=l28 lab=VSS}
C {inv_hv.sym} 0 400 0 0 {name=XNA1}
C {lab_pin.sym} -40 400 0 0 {name=l29 lab=A1}
C {lab_pin.sym} 40 400 2 0 {name=l30 lab=A1n}
C {lab_pin.sym} -20 360 0 0 {name=l31 lab=VDD}
C {lab_pin.sym} 20 440 2 0 {name=l32 lab=VSS}
C {inv_hv.sym} 700 400 0 0 {name=XNA2}
C {lab_pin.sym} 660 400 0 0 {name=l33 lab=A2}
C {lab_pin.sym} 740 400 2 0 {name=l34 lab=A2n}
C {lab_pin.sym} 680 360 0 0 {name=l35 lab=VDD}
C {lab_pin.sym} 720 440 2 0 {name=l36 lab=VSS}
C {nand3_hv.sym} 1400 400 0 0 {name=XNZ}
C {lab_pin.sym} 1360 360 0 0 {name=l37 lab=A0n}
C {lab_pin.sym} 1360 400 0 0 {name=l38 lab=A1n}
C {lab_pin.sym} 1360 440 0 0 {name=l39 lab=A2n}
C {lab_pin.sym} 1440 400 2 0 {name=l40 lab=anz}
C {lab_pin.sym} 1380 280 0 0 {name=l41 lab=VDD}
C {lab_pin.sym} 1420 520 2 0 {name=l42 lab=VSS}
C {nor2_hv.sym} 2100 400 0 0 {name=XN10}
C {lab_pin.sym} 2060 380 0 0 {name=l43 lab=s1}
C {lab_pin.sym} 2060 420 0 0 {name=l44 lab=s0}
C {lab_pin.sym} 2140 400 2 0 {name=l45 lab=n10}
C {lab_pin.sym} 2080 320 0 0 {name=l46 lab=VDD}
C {lab_pin.sym} 2120 480 2 0 {name=l47 lab=VSS}
C {nand3_hv.sym} 0 800 0 0 {name=XL0A}
C {lab_pin.sym} -40 760 0 0 {name=l48 lab=TCN}
C {lab_pin.sym} -40 800 0 0 {name=l49 lab=s0n}
C {lab_pin.sym} -40 840 0 0 {name=l50 lab=s1}
C {lab_pin.sym} 40 800 2 0 {name=l51 lab=l0a}
C {lab_pin.sym} -20 680 0 0 {name=l52 lab=VDD}
C {lab_pin.sym} 20 920 2 0 {name=l53 lab=VSS}
C {nand3_hv.sym} 700 800 0 0 {name=XL0B}
C {lab_pin.sym} 660 760 0 0 {name=l54 lab=TCN}
C {lab_pin.sym} 660 800 0 0 {name=l55 lab=s0n}
C {lab_pin.sym} 660 840 0 0 {name=l56 lab=s2}
C {lab_pin.sym} 740 800 2 0 {name=l57 lab=l0b}
C {lab_pin.sym} 680 680 0 0 {name=l58 lab=VDD}
C {lab_pin.sym} 720 920 2 0 {name=l59 lab=VSS}
C {nand2_hv.sym} 1400 800 0 0 {name=XL0C}
C {lab_pin.sym} 1360 780 0 0 {name=l60 lab=A0}
C {lab_pin.sym} 1360 820 0 0 {name=l61 lab=TC}
C {lab_pin.sym} 1440 800 2 0 {name=l62 lab=l0c}
C {lab_pin.sym} 1380 720 0 0 {name=l63 lab=VDD}
C {lab_pin.sym} 1420 880 2 0 {name=l64 lab=VSS}
C {nand3_hv.sym} 2100 800 0 0 {name=XL0Y}
C {lab_pin.sym} 2060 760 0 0 {name=l65 lab=l0a}
C {lab_pin.sym} 2060 800 0 0 {name=l66 lab=l0b}
C {lab_pin.sym} 2060 840 0 0 {name=l67 lab=l0c}
C {lab_pin.sym} 2140 800 2 0 {name=l68 lab=D0}
C {lab_pin.sym} 2080 680 0 0 {name=l69 lab=VDD}
C {lab_pin.sym} 2120 920 2 0 {name=l70 lab=VSS}
C {nand3_hv.sym} 0 1200 0 0 {name=XL1A}
C {lab_pin.sym} -40 1160 0 0 {name=l71 lab=TCN}
C {lab_pin.sym} -40 1200 0 0 {name=l72 lab=s1}
C {lab_pin.sym} -40 1240 0 0 {name=l73 lab=s0}
C {lab_pin.sym} 40 1200 2 0 {name=l74 lab=l1a}
C {lab_pin.sym} -20 1080 0 0 {name=l75 lab=VDD}
C {lab_pin.sym} 20 1320 2 0 {name=l76 lab=VSS}
C {nand3_hv.sym} 700 1200 0 0 {name=XL1B}
C {lab_pin.sym} 660 1160 0 0 {name=l77 lab=TCN}
C {lab_pin.sym} 660 1200 0 0 {name=l78 lab=s2}
C {lab_pin.sym} 660 1240 0 0 {name=l79 lab=n10}
C {lab_pin.sym} 740 1200 2 0 {name=l80 lab=l1b}
C {lab_pin.sym} 680 1080 0 0 {name=l81 lab=VDD}
C {lab_pin.sym} 720 1320 2 0 {name=l82 lab=VSS}
C {nand2_hv.sym} 1400 1200 0 0 {name=XL1C}
C {lab_pin.sym} 1360 1180 0 0 {name=l83 lab=A1}
C {lab_pin.sym} 1360 1220 0 0 {name=l84 lab=TC}
C {lab_pin.sym} 1440 1200 2 0 {name=l85 lab=l1c}
C {lab_pin.sym} 1380 1120 0 0 {name=l86 lab=VDD}
C {lab_pin.sym} 1420 1280 2 0 {name=l87 lab=VSS}
C {nand3_hv.sym} 2100 1200 0 0 {name=XL1Y}
C {lab_pin.sym} 2060 1160 0 0 {name=l88 lab=l1a}
C {lab_pin.sym} 2060 1200 0 0 {name=l89 lab=l1b}
C {lab_pin.sym} 2060 1240 0 0 {name=l90 lab=l1c}
C {lab_pin.sym} 2140 1200 2 0 {name=l91 lab=D1}
C {lab_pin.sym} 2080 1080 0 0 {name=l92 lab=VDD}
C {lab_pin.sym} 2120 1320 2 0 {name=l93 lab=VSS}
C {nand3_hv.sym} 0 1600 0 0 {name=XL2A}
C {lab_pin.sym} -40 1560 0 0 {name=l94 lab=TCN}
C {lab_pin.sym} -40 1600 0 0 {name=l95 lab=s2}
C {lab_pin.sym} -40 1640 0 0 {name=l96 lab=s1}
C {lab_pin.sym} 40 1600 2 0 {name=l97 lab=l2a}
C {lab_pin.sym} -20 1480 0 0 {name=l98 lab=VDD}
C {lab_pin.sym} 20 1720 2 0 {name=l99 lab=VSS}
C {nand3_hv.sym} 700 1600 0 0 {name=XL2B}
C {lab_pin.sym} 660 1560 0 0 {name=l100 lab=TCN}
C {lab_pin.sym} 660 1600 0 0 {name=l101 lab=s2}
C {lab_pin.sym} 660 1640 0 0 {name=l102 lab=s0}
C {lab_pin.sym} 740 1600 2 0 {name=l103 lab=l2b}
C {lab_pin.sym} 680 1480 0 0 {name=l104 lab=VDD}
C {lab_pin.sym} 720 1720 2 0 {name=l105 lab=VSS}
C {nand2_hv.sym} 1400 1600 0 0 {name=XL2C}
C {lab_pin.sym} 1360 1580 0 0 {name=l106 lab=A2}
C {lab_pin.sym} 1360 1620 0 0 {name=l107 lab=TC}
C {lab_pin.sym} 1440 1600 2 0 {name=l108 lab=l2c}
C {lab_pin.sym} 1380 1520 0 0 {name=l109 lab=VDD}
C {lab_pin.sym} 1420 1680 2 0 {name=l110 lab=VSS}
C {nand3_hv.sym} 2100 1600 0 0 {name=XL2Y}
C {lab_pin.sym} 2060 1560 0 0 {name=l111 lab=l2a}
C {lab_pin.sym} 2060 1600 0 0 {name=l112 lab=l2b}
C {lab_pin.sym} 2060 1640 0 0 {name=l113 lab=l2c}
C {lab_pin.sym} 2140 1600 2 0 {name=l114 lab=D2}
C {lab_pin.sym} 2080 1480 0 0 {name=l115 lab=VDD}
C {lab_pin.sym} 2120 1720 2 0 {name=l116 lab=VSS}
C {nand2_hv.sym} 0 2000 0 0 {name=XMA}
C {lab_pin.sym} -40 1980 0 0 {name=l117 lab=TC}
C {lab_pin.sym} -40 2020 0 0 {name=l118 lab=anz}
C {lab_pin.sym} 40 2000 2 0 {name=l119 lab=m1}
C {lab_pin.sym} -20 1920 0 0 {name=l120 lab=VDD}
C {lab_pin.sym} 20 2080 2 0 {name=l121 lab=VSS}
C {nand2_hv.sym} 700 2000 0 0 {name=XMB}
C {lab_pin.sym} 660 1980 0 0 {name=l122 lab=TCN}
C {lab_pin.sym} 660 2020 0 0 {name=l123 lab=s1}
C {lab_pin.sym} 740 2000 2 0 {name=l124 lab=m2}
C {lab_pin.sym} 680 1920 0 0 {name=l125 lab=VDD}
C {lab_pin.sym} 720 2080 2 0 {name=l126 lab=VSS}
C {nand2_hv.sym} 1400 2000 0 0 {name=XMC}
C {lab_pin.sym} 1360 1980 0 0 {name=l127 lab=TCN}
C {lab_pin.sym} 1360 2020 0 0 {name=l128 lab=s2}
C {lab_pin.sym} 1440 2000 2 0 {name=l129 lab=m3}
C {lab_pin.sym} 1380 1920 0 0 {name=l130 lab=VDD}
C {lab_pin.sym} 1420 2080 2 0 {name=l131 lab=VSS}
C {nand3_hv.sym} 2100 2000 0 0 {name=XMY}
C {lab_pin.sym} 2060 1960 0 0 {name=l132 lab=m1}
C {lab_pin.sym} 2060 2000 0 0 {name=l133 lab=m2}
C {lab_pin.sym} 2060 2040 0 0 {name=l134 lab=m3}
C {lab_pin.sym} 2140 2000 2 0 {name=l135 lab=DM}
C {lab_pin.sym} 2080 1880 0 0 {name=l136 lab=VDD}
C {lab_pin.sym} 2120 2120 2 0 {name=l137 lab=VSS}
C {ipin.sym} -900 -200 0 0 {name=p1 lab=CK}
C {ipin.sym} -900 -100 0 0 {name=p2 lab=TC}
C {ipin.sym} -900 0 0 0 {name=p3 lab=TCN}
C {ipin.sym} -900 100 0 0 {name=p4 lab=A0}
C {ipin.sym} -900 200 0 0 {name=p5 lab=A1}
C {ipin.sym} -900 300 0 0 {name=p6 lab=A2}
C {opin.sym} -900 400 0 0 {name=p7 lab=MC}
C {iopin.sym} -900 500 0 0 {name=p8 lab=VDD}
C {iopin.sym} -900 600 0 0 {name=p9 lab=VSS}
