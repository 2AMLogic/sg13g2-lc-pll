v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: pll_top -- integer-N LC PLL loop top: REF -> pfd (pinned sg13g2-pll) -> cp -> loopfilter -> vco -> prescaler -> divider -> pfd FB, lock_detector (pinned sg13g2-pll) on UP/DN. vco is a black-box interface symbol: the pinned sg13g2-vco bytes are never edited, and its netlist (a flat bench, no .subckt) is supplied by the testbench. N = 100 tied here (M = 12, A = 2). VDDV is the VCO supply branch (tie to VDD in a testbench; the isolation network of spec section 5 is not designed here). IREFCP = 20 uA (cp), IREFPS = 50 uA (prescaler and divider tails).
}
G {}
K {}
V {}
S {}
E {}
C {pfd.sym} 0 0 0 0 {name=XPFD}
C {lab_pin.sym} -40 -20 0 0 {name=l1 lab=REF}
C {lab_pin.sym} -40 20 0 0 {name=l2 lab=FB}
C {lab_pin.sym} 40 -20 2 0 {name=l3 lab=UP}
C {lab_pin.sym} 40 20 2 0 {name=l4 lab=DN}
C {lab_pin.sym} -20 -80 0 0 {name=l5 lab=VDD}
C {lab_pin.sym} 20 80 2 0 {name=l6 lab=VSS}
C {cp.sym} 600 0 0 0 {name=XCP}
C {lab_pin.sym} 560 -60 0 0 {name=l7 lab=UP}
C {lab_pin.sym} 560 -20 0 0 {name=l8 lab=DN}
C {lab_pin.sym} 560 20 0 0 {name=l9 lab=IREFCP}
C {lab_pin.sym} 640 -60 2 0 {name=l10 lab=VCP}
C {lab_pin.sym} 600 -160 2 0 {name=l11 lab=VDD}
C {lab_pin.sym} 600 160 2 0 {name=l12 lab=VSS}
C {loopfilter.sym} 1200 0 0 0 {name=XLF}
C {lab_pin.sym} 1160 -60 0 0 {name=l13 lab=VCP}
C {lab_pin.sym} 1240 -60 2 0 {name=l14 lab=VCTRL}
C {lab_pin.sym} 1200 60 2 0 {name=l15 lab=VSS}
C {vco.sym} 1800 0 0 0 {name=XVCO}
C {lab_pin.sym} 1760 -60 0 0 {name=l16 lab=VCTRL}
C {lab_pin.sym} 1840 -60 2 0 {name=l17 lab=VOP}
C {lab_pin.sym} 1840 -20 2 0 {name=l18 lab=VON}
C {lab_pin.sym} 1800 -100 2 0 {name=l19 lab=VDDV}
C {lab_pin.sym} 1800 100 2 0 {name=l20 lab=VSS}
C {prescaler.sym} 2400 0 0 0 {name=XPS}
C {lab_pin.sym} 2360 -60 0 0 {name=l21 lab=VOP}
C {lab_pin.sym} 2360 -20 0 0 {name=l22 lab=VON}
C {lab_pin.sym} 2360 20 0 0 {name=l23 lab=MC}
C {lab_pin.sym} 2360 60 0 0 {name=l24 lab=IREFPS}
C {lab_pin.sym} 2440 -20 2 0 {name=l25 lab=PSP}
C {lab_pin.sym} 2440 20 2 0 {name=l26 lab=PSN}
C {lab_pin.sym} 2400 -140 2 0 {name=l27 lab=VDD}
C {lab_pin.sym} 2400 140 2 0 {name=l28 lab=VSS}
C {divider.sym} 3000 0 0 0 {name=XDIV}
C {lab_pin.sym} 2960 -60 0 0 {name=l29 lab=PSP}
C {lab_pin.sym} 2960 -20 0 0 {name=l30 lab=PSN}
C {lab_pin.sym} 2960 20 0 0 {name=l31 lab=IREFPS}
C {lab_pin.sym} 2960 60 0 0 {name=l32 lab=VSS}
C {lab_pin.sym} 2960 100 0 0 {name=l33 lab=VSS}
C {lab_pin.sym} 2960 140 0 0 {name=l34 lab=VDD}
C {lab_pin.sym} 2960 180 0 0 {name=l35 lab=VDD}
C {lab_pin.sym} 2960 220 0 0 {name=l36 lab=VSS}
C {lab_pin.sym} 2960 260 0 0 {name=l37 lab=VDD}
C {lab_pin.sym} 3040 -60 2 0 {name=l38 lab=MC}
C {lab_pin.sym} 3040 -20 2 0 {name=l39 lab=FB}
C {lab_pin.sym} 3000 -380 2 0 {name=l40 lab=VDD}
C {lab_pin.sym} 3000 380 2 0 {name=l41 lab=VSS}
C {lock_detector.sym} 0 600 0 0 {name=XLD}
C {lab_pin.sym} -40 580 0 0 {name=l42 lab=UP}
C {lab_pin.sym} -40 620 0 0 {name=l43 lab=DN}
C {lab_pin.sym} 40 600 2 0 {name=l44 lab=LOCK}
C {lab_pin.sym} -20 520 0 0 {name=l45 lab=VDD}
C {lab_pin.sym} 20 680 2 0 {name=l46 lab=VSS}
C {ipin.sym} -900 -200 0 0 {name=p1 lab=REF}
C {ipin.sym} -900 -100 0 0 {name=p2 lab=IREFCP}
C {ipin.sym} -900 0 0 0 {name=p3 lab=IREFPS}
C {opin.sym} -900 100 0 0 {name=p4 lab=LOCK}
C {opin.sym} -900 200 0 0 {name=p5 lab=VCTRL}
C {opin.sym} -900 300 0 0 {name=p6 lab=FB}
C {iopin.sym} -900 400 0 0 {name=p7 lab=VDD}
C {iopin.sym} -900 500 0 0 {name=p8 lab=VDDV}
C {iopin.sym} -900 600 0 0 {name=p9 lab=VSS}
