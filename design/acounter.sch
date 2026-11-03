v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: acounter -- swallow counter (state bits s0, s1; SPICE names are case-insensitive, so they must not be a0, a1): 2-bit down counter that holds at 0, loads A[1:0] together with the program counter (TC). MC = (count != 0), now a REGISTERED flop output (issue #61): the prescaler divides by 5 in the /4/5 stage (total /10) for A reference cycles after each load, then by 4 (total /8). N = 10 A + 8 (M - A) = 8 M + 2 A, A in [0, 3] (issue 43 ruling); needs M >= A. Next state is two gates deep: 11 -> 10 -> 01 -> 00 -> 00.
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
C {dff_tg_hv.sym} 1400 0 0 0 {name=XQM}
C {lab_pin.sym} 1360 -20 0 0 {name=l11 lab=DM}
C {lab_pin.sym} 1360 20 0 0 {name=l12 lab=CK}
C {lab_pin.sym} 1440 0 2 0 {name=l13 lab=MC}
C {lab_pin.sym} 1380 -80 0 0 {name=l14 lab=VDD}
C {lab_pin.sym} 1420 80 2 0 {name=l15 lab=VSS}
C {inv_hv.sym} 2100 0 0 0 {name=XS0}
C {lab_pin.sym} 2060 0 0 0 {name=l16 lab=s0}
C {lab_pin.sym} 2140 0 2 0 {name=l17 lab=s0n}
C {lab_pin.sym} 2080 -40 0 0 {name=l18 lab=VDD}
C {lab_pin.sym} 2120 40 2 0 {name=l19 lab=VSS}
C {nand3_hv.sym} 2800 0 0 0 {name=XL0A}
C {lab_pin.sym} 2760 -40 0 0 {name=l20 lab=TCN}
C {lab_pin.sym} 2760 0 0 0 {name=l21 lab=s1}
C {lab_pin.sym} 2760 40 0 0 {name=l22 lab=s0n}
C {lab_pin.sym} 2840 0 2 0 {name=l23 lab=l0a}
C {lab_pin.sym} 2780 -120 0 0 {name=l24 lab=VDD}
C {lab_pin.sym} 2820 120 2 0 {name=l25 lab=VSS}
C {nand2_hv.sym} 3500 0 0 0 {name=XL0B}
C {lab_pin.sym} 3460 -20 0 0 {name=l26 lab=A0}
C {lab_pin.sym} 3460 20 0 0 {name=l27 lab=TC}
C {lab_pin.sym} 3540 0 2 0 {name=l28 lab=l0b}
C {lab_pin.sym} 3480 -80 0 0 {name=l29 lab=VDD}
C {lab_pin.sym} 3520 80 2 0 {name=l30 lab=VSS}
C {nand2_hv.sym} 0 400 0 0 {name=XL0Y}
C {lab_pin.sym} -40 380 0 0 {name=l31 lab=l0a}
C {lab_pin.sym} -40 420 0 0 {name=l32 lab=l0b}
C {lab_pin.sym} 40 400 2 0 {name=l33 lab=D0}
C {lab_pin.sym} -20 320 0 0 {name=l34 lab=VDD}
C {lab_pin.sym} 20 480 2 0 {name=l35 lab=VSS}
C {nand3_hv.sym} 700 400 0 0 {name=XL1A}
C {lab_pin.sym} 660 360 0 0 {name=l36 lab=TCN}
C {lab_pin.sym} 660 400 0 0 {name=l37 lab=s1}
C {lab_pin.sym} 660 440 0 0 {name=l38 lab=s0}
C {lab_pin.sym} 740 400 2 0 {name=l39 lab=l1a}
C {lab_pin.sym} 680 280 0 0 {name=l40 lab=VDD}
C {lab_pin.sym} 720 520 2 0 {name=l41 lab=VSS}
C {nand2_hv.sym} 1400 400 0 0 {name=XL1B}
C {lab_pin.sym} 1360 380 0 0 {name=l42 lab=A1}
C {lab_pin.sym} 1360 420 0 0 {name=l43 lab=TC}
C {lab_pin.sym} 1440 400 2 0 {name=l44 lab=l1b}
C {lab_pin.sym} 1380 320 0 0 {name=l45 lab=VDD}
C {lab_pin.sym} 1420 480 2 0 {name=l46 lab=VSS}
C {nand2_hv.sym} 2100 400 0 0 {name=XL1Y}
C {lab_pin.sym} 2060 380 0 0 {name=l47 lab=l1a}
C {lab_pin.sym} 2060 420 0 0 {name=l48 lab=l1b}
C {lab_pin.sym} 2140 400 2 0 {name=l49 lab=D1}
C {lab_pin.sym} 2080 320 0 0 {name=l50 lab=VDD}
C {lab_pin.sym} 2120 480 2 0 {name=l51 lab=VSS}
C {inv_hv.sym} 2800 400 0 0 {name=XNA0}
C {lab_pin.sym} 2760 400 0 0 {name=l52 lab=A0}
C {lab_pin.sym} 2840 400 2 0 {name=l53 lab=A0n}
C {lab_pin.sym} 2780 360 0 0 {name=l54 lab=VDD}
C {lab_pin.sym} 2820 440 2 0 {name=l55 lab=VSS}
C {inv_hv.sym} 3500 400 0 0 {name=XNA1}
C {lab_pin.sym} 3460 400 0 0 {name=l56 lab=A1}
C {lab_pin.sym} 3540 400 2 0 {name=l57 lab=A1n}
C {lab_pin.sym} 3480 360 0 0 {name=l58 lab=VDD}
C {lab_pin.sym} 3520 440 2 0 {name=l59 lab=VSS}
C {nand2_hv.sym} 0 800 0 0 {name=XNZ}
C {lab_pin.sym} -40 780 0 0 {name=l60 lab=A0n}
C {lab_pin.sym} -40 820 0 0 {name=l61 lab=A1n}
C {lab_pin.sym} 40 800 2 0 {name=l62 lab=anz}
C {lab_pin.sym} -20 720 0 0 {name=l63 lab=VDD}
C {lab_pin.sym} 20 880 2 0 {name=l64 lab=VSS}
C {nand2_hv.sym} 700 800 0 0 {name=XMA}
C {lab_pin.sym} 660 780 0 0 {name=l65 lab=TC}
C {lab_pin.sym} 660 820 0 0 {name=l66 lab=anz}
C {lab_pin.sym} 740 800 2 0 {name=l67 lab=m1}
C {lab_pin.sym} 680 720 0 0 {name=l68 lab=VDD}
C {lab_pin.sym} 720 880 2 0 {name=l69 lab=VSS}
C {nand2_hv.sym} 1400 800 0 0 {name=XMB}
C {lab_pin.sym} 1360 780 0 0 {name=l70 lab=TCN}
C {lab_pin.sym} 1360 820 0 0 {name=l71 lab=s1}
C {lab_pin.sym} 1440 800 2 0 {name=l72 lab=m2}
C {lab_pin.sym} 1380 720 0 0 {name=l73 lab=VDD}
C {lab_pin.sym} 1420 880 2 0 {name=l74 lab=VSS}
C {nand2_hv.sym} 2100 800 0 0 {name=XMY}
C {lab_pin.sym} 2060 780 0 0 {name=l75 lab=m1}
C {lab_pin.sym} 2060 820 0 0 {name=l76 lab=m2}
C {lab_pin.sym} 2140 800 2 0 {name=l77 lab=DM}
C {lab_pin.sym} 2080 720 0 0 {name=l78 lab=VDD}
C {lab_pin.sym} 2120 880 2 0 {name=l79 lab=VSS}
C {ipin.sym} -900 -200 0 0 {name=p1 lab=CK}
C {ipin.sym} -900 -100 0 0 {name=p2 lab=TC}
C {ipin.sym} -900 0 0 0 {name=p3 lab=TCN}
C {ipin.sym} -900 100 0 0 {name=p4 lab=A0}
C {ipin.sym} -900 200 0 0 {name=p5 lab=A1}
C {opin.sym} -900 300 0 0 {name=p6 lab=MC}
C {iopin.sym} -900 400 0 0 {name=p7 lab=VDD}
C {iopin.sym} -900 500 0 0 {name=p8 lab=VSS}
