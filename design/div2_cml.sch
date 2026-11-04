v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: div2_cml -- fixed divide-by-2 CML first stage on npn13G2v: input emitter followers, master + slave latch with crossed feedback
}
G {}
K {}
V {}
S {}
E {}
C {div2_ef_hs.sym} 400 0 0 0 {name=XEF}
C {lab_pin.sym} 360 -40 0 0 {name=l1 lab=INP}
C {lab_pin.sym} 360 0 0 0 {name=l2 lab=INN}
C {lab_pin.sym} 360 40 0 0 {name=l3 lab=IB}
C {lab_pin.sym} 440 -20 2 0 {name=l4 lab=CKP}
C {lab_pin.sym} 440 20 2 0 {name=l5 lab=CKN}
C {lab_pin.sym} 400 -120 2 0 {name=l6 lab=VDD}
C {lab_pin.sym} 400 120 2 0 {name=l7 lab=VSS}
C {div2_latch_hs.sym} 800 0 0 0 {name=XM}
C {lab_pin.sym} 760 -80 0 0 {name=l8 lab=QN}
C {lab_pin.sym} 760 -40 0 0 {name=l9 lab=QP}
C {lab_pin.sym} 760 0 0 0 {name=l10 lab=CKP}
C {lab_pin.sym} 760 40 0 0 {name=l11 lab=CKN}
C {lab_pin.sym} 760 80 0 0 {name=l12 lab=IB}
C {lab_pin.sym} 840 -20 2 0 {name=l13 lab=MP}
C {lab_pin.sym} 840 20 2 0 {name=l14 lab=MN}
C {lab_pin.sym} 800 -160 2 0 {name=l15 lab=VDD}
C {lab_pin.sym} 800 160 2 0 {name=l16 lab=VSS}
C {div2_latch_hs.sym} 1200 0 0 0 {name=XS}
C {lab_pin.sym} 1160 -80 0 0 {name=l17 lab=MP}
C {lab_pin.sym} 1160 -40 0 0 {name=l18 lab=MN}
C {lab_pin.sym} 1160 0 0 0 {name=l19 lab=CKN}
C {lab_pin.sym} 1160 40 0 0 {name=l20 lab=CKP}
C {lab_pin.sym} 1160 80 0 0 {name=l21 lab=IB}
C {lab_pin.sym} 1240 -20 2 0 {name=l22 lab=QP}
C {lab_pin.sym} 1240 20 2 0 {name=l23 lab=QN}
C {lab_pin.sym} 1200 -160 2 0 {name=l24 lab=VDD}
C {lab_pin.sym} 1200 160 2 0 {name=l25 lab=VSS}
C {ipin.sym} -400 0 0 0 {name=p1 lab=INP}
C {ipin.sym} -400 100 0 0 {name=p2 lab=INN}
C {ipin.sym} -400 200 0 0 {name=p3 lab=IB}
C {opin.sym} 1400 0 0 0 {name=p4 lab=QP}
C {opin.sym} 1400 100 0 0 {name=p5 lab=QN}
C {iopin.sym} -400 -300 0 0 {name=p6 lab=VDD}
C {iopin.sym} -400 -400 0 0 {name=p7 lab=VSS}
