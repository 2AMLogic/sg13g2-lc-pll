v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: acounter -- swallow counter (state bits s0, s1; SPICE names are case-insensitive, so they must not be a0, a1): 2-bit down counter that holds at 0, loads A[1:0] together with the program counter (TC). MC = (count != 0): the prescaler divides by 5 in the /4/5 stage (total /10) for A reference cycles after each load, then by 4 (total /8). N = 10 A + 8 (M - A) = 8 M + 2 A, A in [0, 3] (issue 43 ruling); needs M >= A.
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
C {dff_tg_hv.sym} 600 0 0 0 {name=XQ1}
C {lab_pin.sym} 560 -20 0 0 {name=l6 lab=D1}
C {lab_pin.sym} 560 20 0 0 {name=l7 lab=CK}
C {lab_pin.sym} 640 0 2 0 {name=l8 lab=s1}
C {lab_pin.sym} 580 -80 0 0 {name=l9 lab=VDD}
C {lab_pin.sym} 620 80 2 0 {name=l10 lab=VSS}
C {nor2_hv.sym} 1200 0 0 0 {name=XZ1}
C {lab_pin.sym} 1160 -20 0 0 {name=l11 lab=s0}
C {lab_pin.sym} 1160 20 0 0 {name=l12 lab=s1}
C {lab_pin.sym} 1240 0 2 0 {name=l13 lab=zb}
C {lab_pin.sym} 1180 -80 0 0 {name=l14 lab=VDD}
C {lab_pin.sym} 1220 80 2 0 {name=l15 lab=VSS}
C {inv_hv.sym} 1800 0 0 0 {name=XZ2}
C {lab_pin.sym} 1760 0 0 0 {name=l16 lab=zb}
C {lab_pin.sym} 1840 0 2 0 {name=l17 lab=MC}
C {lab_pin.sym} 1780 -40 0 0 {name=l18 lab=VDD}
C {lab_pin.sym} 1820 40 2 0 {name=l19 lab=VSS}
C {xor2_hv.sym} 2400 0 0 0 {name=XD0}
C {lab_pin.sym} 2360 -20 0 0 {name=l20 lab=s0}
C {lab_pin.sym} 2360 20 0 0 {name=l21 lab=MC}
C {lab_pin.sym} 2440 0 2 0 {name=l22 lab=dec0}
C {lab_pin.sym} 2380 -80 0 0 {name=l23 lab=VDD}
C {lab_pin.sym} 2420 80 2 0 {name=l24 lab=VSS}
C {nor2_hv.sym} 3000 0 0 0 {name=XD1A}
C {lab_pin.sym} 2960 -20 0 0 {name=l25 lab=s0}
C {lab_pin.sym} 2960 20 0 0 {name=l26 lab=zb}
C {lab_pin.sym} 3040 0 2 0 {name=l27 lab=brw}
C {lab_pin.sym} 2980 -80 0 0 {name=l28 lab=VDD}
C {lab_pin.sym} 3020 80 2 0 {name=l29 lab=VSS}
C {xor2_hv.sym} 0 600 0 0 {name=XD1}
C {lab_pin.sym} -40 580 0 0 {name=l30 lab=s1}
C {lab_pin.sym} -40 620 0 0 {name=l31 lab=brw}
C {lab_pin.sym} 40 600 2 0 {name=l32 lab=dec1}
C {lab_pin.sym} -20 520 0 0 {name=l33 lab=VDD}
C {lab_pin.sym} 20 680 2 0 {name=l34 lab=VSS}
C {nand2_hv.sym} 600 600 0 0 {name=XNL0A}
C {lab_pin.sym} 560 580 0 0 {name=l35 lab=dec0}
C {lab_pin.sym} 560 620 0 0 {name=l36 lab=TCN}
C {lab_pin.sym} 640 600 2 0 {name=l37 lab=L0_na}
C {lab_pin.sym} 580 520 0 0 {name=l38 lab=VDD}
C {lab_pin.sym} 620 680 2 0 {name=l39 lab=VSS}
C {nand2_hv.sym} 1200 600 0 0 {name=XNL0B}
C {lab_pin.sym} 1160 580 0 0 {name=l40 lab=A0}
C {lab_pin.sym} 1160 620 0 0 {name=l41 lab=TC}
C {lab_pin.sym} 1240 600 2 0 {name=l42 lab=L0_nb}
C {lab_pin.sym} 1180 520 0 0 {name=l43 lab=VDD}
C {lab_pin.sym} 1220 680 2 0 {name=l44 lab=VSS}
C {nand2_hv.sym} 1800 600 0 0 {name=XNL0Y}
C {lab_pin.sym} 1760 580 0 0 {name=l45 lab=L0_na}
C {lab_pin.sym} 1760 620 0 0 {name=l46 lab=L0_nb}
C {lab_pin.sym} 1840 600 2 0 {name=l47 lab=D0}
C {lab_pin.sym} 1780 520 0 0 {name=l48 lab=VDD}
C {lab_pin.sym} 1820 680 2 0 {name=l49 lab=VSS}
C {nand2_hv.sym} 2400 600 0 0 {name=XNL1A}
C {lab_pin.sym} 2360 580 0 0 {name=l50 lab=dec1}
C {lab_pin.sym} 2360 620 0 0 {name=l51 lab=TCN}
C {lab_pin.sym} 2440 600 2 0 {name=l52 lab=L1_na}
C {lab_pin.sym} 2380 520 0 0 {name=l53 lab=VDD}
C {lab_pin.sym} 2420 680 2 0 {name=l54 lab=VSS}
C {nand2_hv.sym} 3000 600 0 0 {name=XNL1B}
C {lab_pin.sym} 2960 580 0 0 {name=l55 lab=A1}
C {lab_pin.sym} 2960 620 0 0 {name=l56 lab=TC}
C {lab_pin.sym} 3040 600 2 0 {name=l57 lab=L1_nb}
C {lab_pin.sym} 2980 520 0 0 {name=l58 lab=VDD}
C {lab_pin.sym} 3020 680 2 0 {name=l59 lab=VSS}
C {nand2_hv.sym} 0 1200 0 0 {name=XNL1Y}
C {lab_pin.sym} -40 1180 0 0 {name=l60 lab=L1_na}
C {lab_pin.sym} -40 1220 0 0 {name=l61 lab=L1_nb}
C {lab_pin.sym} 40 1200 2 0 {name=l62 lab=D1}
C {lab_pin.sym} -20 1120 0 0 {name=l63 lab=VDD}
C {lab_pin.sym} 20 1280 2 0 {name=l64 lab=VSS}
C {ipin.sym} -900 -200 0 0 {name=p1 lab=CK}
C {ipin.sym} -900 -100 0 0 {name=p2 lab=TC}
C {ipin.sym} -900 0 0 0 {name=p3 lab=TCN}
C {ipin.sym} -900 100 0 0 {name=p4 lab=A0}
C {ipin.sym} -900 200 0 0 {name=p5 lab=A1}
C {opin.sym} -900 300 0 0 {name=p6 lab=MC}
C {iopin.sym} -900 400 0 0 {name=p7 lab=VDD}
C {iopin.sym} -900 500 0 0 {name=p8 lab=VSS}
