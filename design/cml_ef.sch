v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: cml_ef -- emitter-follower pair level shifter (one Vbe down)
}
G {}
K {}
V {}
S {}
E {}
C {sg13g2_pr/npn13G2v.sym} 400 0 0 0 {name=QE1 model=npn13G2v Nx=1 El=1 spiceprefix=X}
C {lab_pin.sym} 420 -30 2 0 {name=l1 lab=VDD}
C {lab_pin.sym} 380 0 0 0 {name=l2 lab=IN}
C {lab_pin.sym} 420 30 2 0 {name=l3 lab=OUT}
C {lab_pin.sym} 420 0 2 0 {name=l4 lab=VSS}
C {sg13g2_pr/npn13G2v.sym} 800 0 0 0 {name=QE2 model=npn13G2v Nx=1 El=1 spiceprefix=X}
C {lab_pin.sym} 820 -30 2 0 {name=l5 lab=VDD}
C {lab_pin.sym} 780 0 0 0 {name=l6 lab=INB}
C {lab_pin.sym} 820 30 2 0 {name=l7 lab=OUTB}
C {lab_pin.sym} 820 0 2 0 {name=l8 lab=VSS}
C {sg13g2_pr/npn13G2v.sym} 1200 0 0 0 {name=QF1 model=npn13G2v Nx=1 El=1 spiceprefix=X}
C {lab_pin.sym} 1220 -30 2 0 {name=l9 lab=qc1}
C {lab_pin.sym} 1180 0 0 0 {name=l10 lab=IB}
C {lab_pin.sym} 1220 30 2 0 {name=l11 lab=f1}
C {lab_pin.sym} 1220 0 2 0 {name=l12 lab=VSS}
C {sg13g2_pr/rppd.sym} 1600 0 0 0 {name=RF1 model=rppd body=VSS spiceprefix=X w=1u b=0 m=1 l=9.05u}
C {lab_pin.sym} 1600 -30 2 0 {name=l13 lab=f1}
C {lab_pin.sym} 1600 30 2 0 {name=l14 lab=VSS}
C {sg13g2_pr/npn13G2v.sym} 2000 0 0 0 {name=QF2 model=npn13G2v Nx=1 El=1 spiceprefix=X}
C {lab_pin.sym} 2020 -30 2 0 {name=l15 lab=qc2}
C {lab_pin.sym} 1980 0 0 0 {name=l16 lab=IB}
C {lab_pin.sym} 2020 30 2 0 {name=l17 lab=f2}
C {lab_pin.sym} 2020 0 2 0 {name=l18 lab=VSS}
C {sg13g2_pr/rppd.sym} 2400 0 0 0 {name=RF2 model=rppd body=VSS spiceprefix=X w=1u b=0 m=1 l=9.05u}
C {lab_pin.sym} 2400 -30 2 0 {name=l19 lab=f2}
C {lab_pin.sym} 2400 30 2 0 {name=l20 lab=VSS}
C {sg13g2_pr/npn13G2v.sym} 1200 -200 0 0 {name=DF1 model=npn13G2v Nx=1 El=1 spiceprefix=X}
C {lab_pin.sym} 1220 -230 2 0 {name=l110 lab=OUT}
C {lab_pin.sym} 1180 -200 0 0 {name=l111 lab=OUT}
C {lab_pin.sym} 1220 -170 2 0 {name=l112 lab=d1}
C {lab_pin.sym} 1220 -200 2 0 {name=l113 lab=VSS}
C {sg13g2_pr/npn13G2v.sym} 2000 -200 0 0 {name=DF2 model=npn13G2v Nx=1 El=1 spiceprefix=X}
C {lab_pin.sym} 2020 -230 2 0 {name=l120 lab=OUTB}
C {lab_pin.sym} 1980 -200 0 0 {name=l121 lab=OUTB}
C {lab_pin.sym} 2020 -170 2 0 {name=l122 lab=d2}
C {lab_pin.sym} 2020 -200 2 0 {name=l123 lab=VSS}
C {sg13g2_pr/rppd.sym} 1600 -200 0 0 {name=RDF1 model=rppd body=VSS spiceprefix=X w=1u b=0 m=1 l=15.3u}
C {lab_pin.sym} 1600 -230 2 0 {name=l210 lab=d1}
C {lab_pin.sym} 1600 -170 2 0 {name=l211 lab=qc1}
C {sg13g2_pr/rppd.sym} 2400 -200 0 0 {name=RDF2 model=rppd body=VSS spiceprefix=X w=1u b=0 m=1 l=15.3u}
C {lab_pin.sym} 2400 -230 2 0 {name=l220 lab=d2}
C {lab_pin.sym} 2400 -170 2 0 {name=l221 lab=qc2}
C {ipin.sym} -400 0 0 0 {name=p1 lab=IN}
C {ipin.sym} -400 100 0 0 {name=p2 lab=INB}
C {ipin.sym} -400 200 0 0 {name=p3 lab=IB}
C {opin.sym} 1400 0 0 0 {name=p4 lab=OUT}
C {opin.sym} 1400 100 0 0 {name=p5 lab=OUTB}
C {iopin.sym} -400 -300 0 0 {name=p6 lab=VDD}
C {iopin.sym} -400 -400 0 0 {name=p7 lab=VSS}
