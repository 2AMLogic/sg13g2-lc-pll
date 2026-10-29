v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: prescaler -- prescaler: fixed /2 CML first stage on the VCO tank, then /4/5 dual-modulus (P = 8 or 9). IREF = 50 uA sets every tail as k * IREF.
}
G {}
K {}
V {}
S {}
E {}
C {sg13g2_pr/npn13G2v.sym} 400 0 0 0 {name=QREF model=npn13G2v Nx=1 El=1 spiceprefix=X}
C {lab_pin.sym} 420 -30 2 0 {name=l1 lab=IREF}
C {lab_pin.sym} 380 0 0 0 {name=l2 lab=IREF}
C {lab_pin.sym} 420 30 2 0 {name=l3 lab=reref}
C {lab_pin.sym} 420 0 2 0 {name=l4 lab=VSS}
C {res.sym} 800 0 0 0 {name=RREF value=2400 footprint=1206 device=resistor m=1}
C {lab_pin.sym} 800 -30 2 0 {name=l5 lab=reref}
C {lab_pin.sym} 800 30 2 0 {name=l6 lab=VSS}
C {div2_cml.sym} 1200 0 0 0 {name=X2}
C {lab_pin.sym} 1160 -40 0 0 {name=l7 lab=INP}
C {lab_pin.sym} 1160 0 0 0 {name=l8 lab=INN}
C {lab_pin.sym} 1160 40 0 0 {name=l9 lab=IREF}
C {lab_pin.sym} 1240 -20 2 0 {name=l10 lab=HP}
C {lab_pin.sym} 1240 20 2 0 {name=l11 lab=HN}
C {lab_pin.sym} 1200 -120 2 0 {name=l12 lab=VDD}
C {lab_pin.sym} 1200 120 2 0 {name=l13 lab=VSS}
C {div45_dm.sym} 1600 0 0 0 {name=X45}
C {lab_pin.sym} 1560 -60 0 0 {name=l14 lab=HP}
C {lab_pin.sym} 1560 -20 0 0 {name=l15 lab=HN}
C {lab_pin.sym} 1560 20 0 0 {name=l16 lab=MC}
C {lab_pin.sym} 1560 60 0 0 {name=l17 lab=IREF}
C {lab_pin.sym} 1640 -20 2 0 {name=l18 lab=OUTP}
C {lab_pin.sym} 1640 20 2 0 {name=l19 lab=OUTN}
C {lab_pin.sym} 1600 -140 2 0 {name=l20 lab=VDD}
C {lab_pin.sym} 1600 140 2 0 {name=l21 lab=VSS}
C {ipin.sym} -400 0 0 0 {name=p1 lab=INP}
C {ipin.sym} -400 100 0 0 {name=p2 lab=INN}
C {ipin.sym} -400 200 0 0 {name=p3 lab=MC}
C {ipin.sym} -400 300 0 0 {name=p4 lab=IREF}
C {opin.sym} 1400 0 0 0 {name=p5 lab=OUTP}
C {opin.sym} 1400 100 0 0 {name=p6 lab=OUTN}
C {iopin.sym} -400 -300 0 0 {name=p7 lab=VDD}
C {iopin.sym} -400 -400 0 0 {name=p8 lab=VSS}
