v {xschem version=3.4.8RC file_version=1.3
sg13g2-lc-pll :: loopfilter -- type-II 3rd-order passive filter from sim/loop-model/loop-filter.json: series R1-C1, shunt C2, unloaded R3-C3 pole. VIN = charge-pump output, VCTRL = VCO control. Values: R1 = R3 = 7035.6 ohm, C1 = 90.48 pF, C2 = 6.032 pF, C3 = 2.828 pF. Poly resistors are rppd (260 ohm/sq, w = 2 um), capacitors cap_cmim at 1.5 fF/um2 nominal (C1 = 12 x 70.9 um square, each under the 8 pF PCell limit); sized by square count and area density only, not yet by a model run. No on-chip trim.
}
G {}
K {}
V {}
S {}
E {}
C {sg13g2_pr/rppd.sym} 0 0 0 0 {name=R1 model=rppd body=VSS spiceprefix=X w=2u b=0 m=1 l=53.9u}
C {lab_pin.sym} 0 -30 2 0 {name=l1 lab=VIN}
C {lab_pin.sym} 0 30 2 0 {name=l2 lab=nz1}
C {sg13g2_pr/cap_cmim.sym} 600 0 0 0 {name=C1 model=cap_cmim w=70.9u l=70.9u m=12 spiceprefix=X}
C {lab_pin.sym} 600 -30 2 0 {name=l3 lab=nz1}
C {lab_pin.sym} 600 30 2 0 {name=l4 lab=VSS}
C {sg13g2_pr/cap_cmim.sym} 1200 0 0 0 {name=C2 model=cap_cmim w=63.4u l=63.4u m=1 spiceprefix=X}
C {lab_pin.sym} 1200 -30 2 0 {name=l5 lab=VIN}
C {lab_pin.sym} 1200 30 2 0 {name=l6 lab=VSS}
C {sg13g2_pr/rppd.sym} 1800 0 0 0 {name=R3 model=rppd body=VSS spiceprefix=X w=2u b=0 m=1 l=53.9u}
C {lab_pin.sym} 1800 -30 2 0 {name=l7 lab=VIN}
C {lab_pin.sym} 1800 30 2 0 {name=l8 lab=VCTRL}
C {sg13g2_pr/cap_cmim.sym} 2400 0 0 0 {name=C3 model=cap_cmim w=43.4u l=43.4u m=1 spiceprefix=X}
C {lab_pin.sym} 2400 -30 2 0 {name=l9 lab=VCTRL}
C {lab_pin.sym} 2400 30 2 0 {name=l10 lab=VSS}
C {ipin.sym} -900 -200 0 0 {name=p1 lab=VIN}
C {opin.sym} -900 -100 0 0 {name=p2 lab=VCTRL}
C {iopin.sym} -900 0 0 0 {name=p3 lab=VSS}
