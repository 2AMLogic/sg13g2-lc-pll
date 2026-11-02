v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: cml_and2 -- two-level CML AND: A pair on top (latch-output level), B pair below (one Vbe lower, from cml_ef)
}
G {}
K {}
V {}
S {}
E {}
C {res.sym} 400 0 0 0 {name=RL1 value=2400 footprint=1206 device=resistor m=1}
C {lab_pin.sym} 400 -30 2 0 {name=l1 lab=VDD}
C {lab_pin.sym} 400 30 2 0 {name=l2 lab=Q}
C {res.sym} 800 0 0 0 {name=RL2 value=2400 footprint=1206 device=resistor m=1}
C {lab_pin.sym} 800 -30 2 0 {name=l3 lab=VDD}
C {lab_pin.sym} 800 30 2 0 {name=l4 lab=QB}
C {sg13g2_pr/npn13G2v.sym} 1200 0 0 0 {name=QA1 model=npn13G2v Nx=1 El=1 spiceprefix=X}
C {lab_pin.sym} 1220 -30 2 0 {name=l5 lab=QB}
C {lab_pin.sym} 1180 0 0 0 {name=l6 lab=A}
C {lab_pin.sym} 1220 30 2 0 {name=l7 lab=n1}
C {lab_pin.sym} 1220 0 2 0 {name=l8 lab=VSS}
C {sg13g2_pr/npn13G2v.sym} 1600 0 0 0 {name=QA2 model=npn13G2v Nx=1 El=1 spiceprefix=X}
C {lab_pin.sym} 1620 -30 2 0 {name=l9 lab=Q}
C {lab_pin.sym} 1580 0 0 0 {name=l10 lab=AB}
C {lab_pin.sym} 1620 30 2 0 {name=l11 lab=n1}
C {lab_pin.sym} 1620 0 2 0 {name=l12 lab=VSS}
C {sg13g2_pr/npn13G2v.sym} 2000 0 0 0 {name=QB1 model=npn13G2v Nx=1 El=1 spiceprefix=X}
C {lab_pin.sym} 2020 -30 2 0 {name=l13 lab=n1}
C {lab_pin.sym} 1980 0 0 0 {name=l14 lab=B}
C {lab_pin.sym} 2020 30 2 0 {name=l15 lab=t}
C {lab_pin.sym} 2020 0 2 0 {name=l16 lab=VSS}
C {sg13g2_pr/npn13G2v.sym} 2400 0 0 0 {name=QB2 model=npn13G2v Nx=1 El=1 spiceprefix=X}
C {lab_pin.sym} 2420 -30 2 0 {name=l17 lab=Q}
C {lab_pin.sym} 2380 0 0 0 {name=l18 lab=BB}
C {lab_pin.sym} 2420 30 2 0 {name=l19 lab=t}
C {lab_pin.sym} 2420 0 2 0 {name=l20 lab=VSS}
C {sg13g2_pr/npn13G2v.sym} 400 400 0 0 {name=QT model=npn13G2v Nx=2 El=1 spiceprefix=X}
C {lab_pin.sym} 420 370 2 0 {name=l21 lab=t}
C {lab_pin.sym} 380 400 0 0 {name=l22 lab=IB}
C {lab_pin.sym} 420 430 2 0 {name=l23 lab=teT}
C {lab_pin.sym} 420 400 2 0 {name=l24 lab=VSS}
C {res.sym} 800 400 0 0 {name=RT value=1200 footprint=1206 device=resistor m=1}
C {lab_pin.sym} 800 370 2 0 {name=l25 lab=teT}
C {lab_pin.sym} 800 430 2 0 {name=l26 lab=VSS}
C {ipin.sym} -400 0 0 0 {name=p1 lab=A}
C {ipin.sym} -400 100 0 0 {name=p2 lab=AB}
C {ipin.sym} -400 200 0 0 {name=p3 lab=B}
C {ipin.sym} -400 300 0 0 {name=p4 lab=BB}
C {ipin.sym} -400 400 0 0 {name=p5 lab=IB}
C {opin.sym} 1400 0 0 0 {name=p6 lab=Q}
C {opin.sym} 1400 100 0 0 {name=p7 lab=QB}
C {iopin.sym} -400 -300 0 0 {name=p8 lab=VDD}
C {iopin.sym} -400 -400 0 0 {name=p9 lab=VSS}
