v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: cml2cmos -- CML (prescaler OUTP/OUTN, common mode near VDD) to CMOS clock: AC-coupled (0.29 pF MIM) HV-NMOS differential pair biased at VDD/2 (ideal 50 k resistors, like the prescaler's), PMOS mirror load, tail 4 x IREF from the prescaler reference node (Nx = 4 npn13G2v + 600 ohm, the same k x IREF rule as the prescaler), two pinned inv_hv. Issue #97: the first inverter is AC-coupled from cmo (0.095 pF MIM) and self-biased by a 100 k feedback resistor from cmob, so its switching point tracks the cmo common mode (60-65 % of VDD at the failing corners) and the clock keeps a 50 % duty. Coupling is needed because a DC-coupled NMOS pair at the CML common mode (about 3.2 V) puts its tail near 1.8 V and the low output never reaches the inverter threshold. Sized by hand, checked at one corner only (see design/README.md).
}
G {}
K {}
V {}
S {}
E {}
C {sg13g2_pr/npn13G2v.sym} 0 0 0 0 {name=QT model=npn13G2v Nx=4 El=1 spiceprefix=X}
C {lab_pin.sym} 20 -30 2 0 {name=l1 lab=tail}
C {lab_pin.sym} -20 0 0 0 {name=l2 lab=IREF}
C {lab_pin.sym} 20 30 2 0 {name=l3 lab=te}
C {lab_pin.sym} 20 0 2 0 {name=l4 lab=VSS}
C {res.sym} 600 0 0 0 {name=RT value=600 footprint=1206 device=resistor m=1}
C {lab_pin.sym} 600 -30 2 0 {name=l5 lab=te}
C {lab_pin.sym} 600 30 2 0 {name=l6 lab=VSS}
C {sg13g2_pr/cap_cmim.sym} 1200 0 0 0 {name=CC1 model=cap_cmim w=14u l=14u m=1 spiceprefix=X}
C {lab_pin.sym} 1200 -30 2 0 {name=l7 lab=INP}
C {lab_pin.sym} 1200 30 2 0 {name=l8 lab=gp}
C {sg13g2_pr/cap_cmim.sym} 1800 0 0 0 {name=CC2 model=cap_cmim w=14u l=14u m=1 spiceprefix=X}
C {lab_pin.sym} 1800 -30 2 0 {name=l9 lab=INN}
C {lab_pin.sym} 1800 30 2 0 {name=l10 lab=gn}
C {res.sym} 2400 0 0 0 {name=RB1 value=50k footprint=1206 device=resistor m=1}
C {lab_pin.sym} 2400 -30 2 0 {name=l11 lab=vb}
C {lab_pin.sym} 2400 30 2 0 {name=l12 lab=gp}
C {res.sym} 3000 0 0 0 {name=RB2 value=50k footprint=1206 device=resistor m=1}
C {lab_pin.sym} 3000 -30 2 0 {name=l13 lab=vb}
C {lab_pin.sym} 3000 30 2 0 {name=l14 lab=gn}
C {res.sym} 0 600 0 0 {name=RV1 value=50k footprint=1206 device=resistor m=1}
C {lab_pin.sym} 0 570 2 0 {name=l15 lab=VDD}
C {lab_pin.sym} 0 630 2 0 {name=l16 lab=vb}
C {res.sym} 600 600 0 0 {name=RV2 value=50k footprint=1206 device=resistor m=1}
C {lab_pin.sym} 600 570 2 0 {name=l17 lab=vb}
C {lab_pin.sym} 600 630 2 0 {name=l18 lab=VSS}
C {sg13g2_pr/sg13_hv_nmos.sym} 1200 600 0 0 {name=M1 model=sg13_hv_nmos ng=1 m=1 spiceprefix=X w=10u l=0.5u}
C {lab_pin.sym} 1220 570 2 0 {name=l19 lab=d1}
C {lab_pin.sym} 1180 600 0 0 {name=l20 lab=gp}
C {lab_pin.sym} 1220 630 2 0 {name=l21 lab=tail}
C {lab_pin.sym} 1220 600 2 0 {name=l22 lab=VSS}
C {sg13g2_pr/sg13_hv_nmos.sym} 1800 600 0 0 {name=M2 model=sg13_hv_nmos ng=1 m=1 spiceprefix=X w=10u l=0.5u}
C {lab_pin.sym} 1820 570 2 0 {name=l23 lab=cmo}
C {lab_pin.sym} 1780 600 0 0 {name=l24 lab=gn}
C {lab_pin.sym} 1820 630 2 0 {name=l25 lab=tail}
C {lab_pin.sym} 1820 600 2 0 {name=l26 lab=VSS}
C {sg13g2_pr/sg13_hv_pmos.sym} 2400 600 0 0 {name=P1 model=sg13_hv_pmos ng=1 m=1 spiceprefix=X w=10u l=0.5u}
C {lab_pin.sym} 2420 630 2 0 {name=l27 lab=d1}
C {lab_pin.sym} 2380 600 0 0 {name=l28 lab=d1}
C {lab_pin.sym} 2420 570 2 0 {name=l29 lab=VDD}
C {lab_pin.sym} 2420 600 2 0 {name=l30 lab=VDD}
C {sg13g2_pr/sg13_hv_pmos.sym} 3000 600 0 0 {name=P2 model=sg13_hv_pmos ng=1 m=1 spiceprefix=X w=10u l=0.5u}
C {lab_pin.sym} 3020 630 2 0 {name=l31 lab=cmo}
C {lab_pin.sym} 2980 600 0 0 {name=l32 lab=d1}
C {lab_pin.sym} 3020 570 2 0 {name=l33 lab=VDD}
C {lab_pin.sym} 3020 600 2 0 {name=l34 lab=VDD}
C {inv_hv.sym} 0 1200 0 0 {name=XI1}
C {lab_pin.sym} -40 1200 0 0 {name=l35 lab=xin}
C {lab_pin.sym} 40 1200 2 0 {name=l36 lab=cmob}
C {lab_pin.sym} -20 1160 0 0 {name=l37 lab=VDD}
C {lab_pin.sym} 20 1240 2 0 {name=l38 lab=VSS}
C {inv_hv.sym} 600 1200 0 0 {name=XI2}
C {lab_pin.sym} 560 1200 0 0 {name=l39 lab=cmob}
C {lab_pin.sym} 640 1200 2 0 {name=l40 lab=CK}
C {lab_pin.sym} 580 1160 0 0 {name=l41 lab=VDD}
C {lab_pin.sym} 620 1240 2 0 {name=l42 lab=VSS}
C {sg13g2_pr/cap_cmim.sym} -600 1200 0 0 {name=CI1 model=cap_cmim w=8u l=8u m=1 spiceprefix=X}
C {lab_pin.sym} -600 1170 2 0 {name=l43 lab=cmo}
C {lab_pin.sym} -600 1230 2 0 {name=l44 lab=xin}
C {res.sym} -300 1200 0 0 {name=RF1 value=100k footprint=1206 device=resistor m=1}
C {lab_pin.sym} -300 1170 2 0 {name=l45 lab=xin}
C {lab_pin.sym} -300 1230 2 0 {name=l46 lab=cmob}
C {ipin.sym} -900 -200 0 0 {name=p1 lab=INP}
C {ipin.sym} -900 -100 0 0 {name=p2 lab=INN}
C {ipin.sym} -900 0 0 0 {name=p3 lab=IREF}
C {opin.sym} -900 100 0 0 {name=p4 lab=CK}
C {iopin.sym} -900 200 0 0 {name=p5 lab=VDD}
C {iopin.sym} -900 300 0 0 {name=p6 lab=VSS}
