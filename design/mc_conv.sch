v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: mc_conv -- CMOS (0/3.3 V) modulus control to CML: base resistor, VDD/2 reference divider, loaded pair
}
G {}
K {}
V {}
S {}
E {}
C {res.sym} 400 0 0 0 {name=RIN value=20k footprint=1206 device=resistor m=1}
C {lab_pin.sym} 400 -30 2 0 {name=l1 lab=MC}
C {lab_pin.sym} 400 30 2 0 {name=l2 lab=bm}
C {res.sym} 800 0 0 0 {name=RD1 value=20k footprint=1206 device=resistor m=1}
C {lab_pin.sym} 800 -30 2 0 {name=l3 lab=VDD}
C {lab_pin.sym} 800 30 2 0 {name=l4 lab=vr}
C {res.sym} 1200 0 0 0 {name=RD2 value=20k footprint=1206 device=resistor m=1}
C {lab_pin.sym} 1200 -30 2 0 {name=l5 lab=vr}
C {lab_pin.sym} 1200 30 2 0 {name=l6 lab=VSS}
C {res.sym} 1600 0 0 0 {name=RL1 value=2400 footprint=1206 device=resistor m=1}
C {lab_pin.sym} 1600 -30 2 0 {name=l7 lab=VDD}
C {lab_pin.sym} 1600 30 2 0 {name=l8 lab=MCP}
C {res.sym} 2000 0 0 0 {name=RL2 value=2400 footprint=1206 device=resistor m=1}
C {lab_pin.sym} 2000 -30 2 0 {name=l9 lab=VDD}
C {lab_pin.sym} 2000 30 2 0 {name=l10 lab=MCN}
C {sg13g2_pr/npn13G2v.sym} 2400 0 0 0 {name=QM1 model=npn13G2v Nx=1 El=1 spiceprefix=X}
C {lab_pin.sym} 2420 -30 2 0 {name=l11 lab=MCN}
C {lab_pin.sym} 2380 0 0 0 {name=l12 lab=bm}
C {lab_pin.sym} 2420 30 2 0 {name=l13 lab=t}
C {lab_pin.sym} 2420 0 2 0 {name=l14 lab=VSS}
C {sg13g2_pr/npn13G2v.sym} 400 400 0 0 {name=QM2 model=npn13G2v Nx=1 El=1 spiceprefix=X}
C {lab_pin.sym} 420 370 2 0 {name=l15 lab=MCP}
C {lab_pin.sym} 380 400 0 0 {name=l16 lab=vr}
C {lab_pin.sym} 420 430 2 0 {name=l17 lab=t}
C {lab_pin.sym} 420 400 2 0 {name=l18 lab=VSS}
C {sg13g2_pr/npn13G2v.sym} 800 400 0 0 {name=QT model=npn13G2v Nx=2 El=1 spiceprefix=X}
C {lab_pin.sym} 820 370 2 0 {name=l19 lab=t}
C {lab_pin.sym} 780 400 0 0 {name=l20 lab=IB}
C {lab_pin.sym} 820 430 2 0 {name=l21 lab=teT}
C {lab_pin.sym} 820 400 2 0 {name=l22 lab=VSS}
C {res.sym} 1200 400 0 0 {name=RT value=1200 footprint=1206 device=resistor m=1}
C {lab_pin.sym} 1200 370 2 0 {name=l23 lab=teT}
C {lab_pin.sym} 1200 430 2 0 {name=l24 lab=VSS}
C {ipin.sym} -400 0 0 0 {name=p1 lab=MC}
C {ipin.sym} -400 100 0 0 {name=p2 lab=IB}
C {opin.sym} 1400 0 0 0 {name=p3 lab=MCP}
C {opin.sym} 1400 100 0 0 {name=p4 lab=MCN}
C {iopin.sym} -400 -300 0 0 {name=p5 lab=VDD}
C {iopin.sym} -400 -400 0 0 {name=p6 lab=VSS}
