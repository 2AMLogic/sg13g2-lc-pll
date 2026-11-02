v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: divider -- post-prescaler divider: CML to CMOS, M/A pulse-swallow counter, retimed feedback pulse. N = 8 M + 2 A (prescaler P = 8/10), A in [0, 3], even N only; N = 100 is M = 12 (1100), A = 2 (10). FB is TC retimed by one CK flop (one CK period wide). IREF is the prescaler reference node.
}
G {}
K {}
V {}
S {}
E {}
C {cml2cmos.sym} 0 0 0 0 {name=XCV}
C {lab_pin.sym} -40 -60 0 0 {name=l1 lab=INP}
C {lab_pin.sym} -40 -20 0 0 {name=l2 lab=INN}
C {lab_pin.sym} -40 20 0 0 {name=l3 lab=IREF}
C {lab_pin.sym} 40 -60 2 0 {name=l4 lab=CK}
C {lab_pin.sym} 0 -140 2 0 {name=l5 lab=VDD}
C {lab_pin.sym} 0 140 2 0 {name=l6 lab=VSS}
C {mcounter.sym} 600 0 0 0 {name=XM}
C {lab_pin.sym} 560 -60 0 0 {name=l7 lab=CK}
C {lab_pin.sym} 560 -20 0 0 {name=l8 lab=M0}
C {lab_pin.sym} 560 20 0 0 {name=l9 lab=M1}
C {lab_pin.sym} 560 60 0 0 {name=l10 lab=M2}
C {lab_pin.sym} 560 100 0 0 {name=l11 lab=M3}
C {lab_pin.sym} 640 -60 2 0 {name=l12 lab=TC}
C {lab_pin.sym} 640 -20 2 0 {name=l13 lab=TCN}
C {lab_pin.sym} 600 -220 2 0 {name=l14 lab=VDD}
C {lab_pin.sym} 600 220 2 0 {name=l15 lab=VSS}
C {acounter.sym} 1200 0 0 0 {name=XA}
C {lab_pin.sym} 1160 -60 0 0 {name=l16 lab=CK}
C {lab_pin.sym} 1160 -20 0 0 {name=l17 lab=TC}
C {lab_pin.sym} 1160 20 0 0 {name=l18 lab=TCN}
C {lab_pin.sym} 1160 60 0 0 {name=l19 lab=A0}
C {lab_pin.sym} 1160 100 0 0 {name=l20 lab=A1}
C {lab_pin.sym} 1240 -60 2 0 {name=l21 lab=MC}
C {lab_pin.sym} 1200 -220 2 0 {name=l22 lab=VDD}
C {lab_pin.sym} 1200 220 2 0 {name=l23 lab=VSS}
C {dff_tg_hv.sym} 1800 0 0 0 {name=XFB}
C {lab_pin.sym} 1760 -20 0 0 {name=l24 lab=TC}
C {lab_pin.sym} 1760 20 0 0 {name=l25 lab=CK}
C {lab_pin.sym} 1840 0 2 0 {name=l26 lab=FB}
C {lab_pin.sym} 1780 -80 0 0 {name=l27 lab=VDD}
C {lab_pin.sym} 1820 80 2 0 {name=l28 lab=VSS}
C {ipin.sym} -900 -200 0 0 {name=p1 lab=INP}
C {ipin.sym} -900 -100 0 0 {name=p2 lab=INN}
C {ipin.sym} -900 0 0 0 {name=p3 lab=IREF}
C {ipin.sym} -900 100 0 0 {name=p4 lab=M0}
C {ipin.sym} -900 200 0 0 {name=p5 lab=M1}
C {ipin.sym} -900 300 0 0 {name=p6 lab=M2}
C {ipin.sym} -900 400 0 0 {name=p7 lab=M3}
C {ipin.sym} -900 500 0 0 {name=p8 lab=A0}
C {ipin.sym} -900 600 0 0 {name=p9 lab=A1}
C {opin.sym} -900 700 0 0 {name=p10 lab=MC}
C {opin.sym} -900 800 0 0 {name=p11 lab=FB}
C {iopin.sym} -900 900 0 0 {name=p12 lab=VDD}
C {iopin.sym} -900 1000 0 0 {name=p13 lab=VSS}
