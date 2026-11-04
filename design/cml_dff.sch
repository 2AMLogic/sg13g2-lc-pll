v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: cml_dff -- master-slave CML D flip-flop (falling edge of CK)
}
G {}
K {}
V {}
S {}
E {}
C {cml_latch.sym} 400 0 0 0 {name=XM}
C {lab_pin.sym} 360 -80 0 0 {name=l1 lab=D}
C {lab_pin.sym} 360 -40 0 0 {name=l2 lab=DB}
C {lab_pin.sym} 360 0 0 0 {name=l3 lab=CK}
C {lab_pin.sym} 360 40 0 0 {name=l4 lab=CKB}
C {lab_pin.sym} 360 80 0 0 {name=l5 lab=IB}
C {lab_pin.sym} 440 -20 2 0 {name=l6 lab=M}
C {lab_pin.sym} 440 20 2 0 {name=l7 lab=MB}
C {lab_pin.sym} 400 -160 2 0 {name=l8 lab=VDD}
C {lab_pin.sym} 400 160 2 0 {name=l9 lab=VSS}
C {cml_latch.sym} 800 0 0 0 {name=XS}
C {lab_pin.sym} 760 -80 0 0 {name=l10 lab=M}
C {lab_pin.sym} 760 -40 0 0 {name=l11 lab=MB}
C {lab_pin.sym} 760 0 0 0 {name=l12 lab=CKB}
C {lab_pin.sym} 760 40 0 0 {name=l13 lab=CK}
C {lab_pin.sym} 760 80 0 0 {name=l14 lab=IB}
C {lab_pin.sym} 840 -20 2 0 {name=l15 lab=Q}
C {lab_pin.sym} 840 20 2 0 {name=l16 lab=QB}
C {lab_pin.sym} 800 -160 2 0 {name=l17 lab=VDD}
C {lab_pin.sym} 800 160 2 0 {name=l18 lab=VSS}
C {ipin.sym} -400 0 0 0 {name=p1 lab=D}
C {ipin.sym} -400 100 0 0 {name=p2 lab=DB}
C {ipin.sym} -400 200 0 0 {name=p3 lab=CK}
C {ipin.sym} -400 300 0 0 {name=p4 lab=CKB}
C {ipin.sym} -400 400 0 0 {name=p5 lab=IB}
C {opin.sym} 1400 0 0 0 {name=p6 lab=Q}
C {opin.sym} 1400 100 0 0 {name=p7 lab=QB}
C {iopin.sym} -400 -300 0 0 {name=p8 lab=VDD}
C {iopin.sym} -400 -400 0 0 {name=p9 lab=VSS}
