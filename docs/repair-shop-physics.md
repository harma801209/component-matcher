# Repair shop: validated equivalent-circuit scope (model v2)

This is **not** a simulation of an OEM lamp/fan/speaker/clock/sensor/router.
These product names frame six explicitly defined low-voltage teaching circuits.
The component picker is a location illustration, NOT an electrical schematic.
The visible netlist, conditions, instrument assumptions and exclusions are the
electrical contract. Values are calculated, not measured on hardware. No SPICE,
hardware certification, thermal qualification or actual repair-safety claim.

## Changes from v1

- Remove authored voltage/waveform arrays from inventory. Failures change model
  parameters; all notes, hints, measurements and acceptance derive from that model.
- Never assign a deterministic low voltage to an unbiased high-impedance input.
  The ideal model reports null/floating. Probe resistance, leakage and initial
  charge would have to be added to predict a physical meter's indication.
- Declare the speaker feedback topology: noninverting, Rf=90kΩ, Rg=R1=10kΩ to
  buffered Vref, not directly to GND. A 100kΩ Rg gives gain1.9 instead of10.
- Compute repair acceptance from the installed candidate, actual circuit results
  and explicit limits; a click/installed flag cannot manufacture a passing result.
- Pause the unsupported crystal-stopped template. Product and failure positions
  remain unchanged, so historical seeds, coins and scores are not relabeled.
  Legacy active crystal orders can be canceled with one refund of a purchased,
  undelivered part. New offers exclude this slot (17 supported templates).

## Equations and domains

All solver units are SI; µF/mA/mV are display conversions. Ideal instruments have
no error, no loading, and declared compliance; real instruments do not. Isolation
is automatic in the game and is not permission to probe or desolder live equipment.

### LED series circuit

25°C, 5V source, fuse0.2Ω, R1=220Ω, redLED. Use
`Vd(I)=n*VT*ln(1+I/Is)+I*Rs`, n=2, VT=.02585V, Rs=2Ω;
Is is calibrated to Vd=2V at20mA. Bisection solves
`5 = I*(R1+.2) + Vd(I)`. This is an authored characteristic, not an OEM LED fit.
Nominal result:13.76824mA,1.96823V LED drop,41.70418mW R1 loss.
R1 drift to2.2kΩ gives1.442mA with1.827V LED drop, not a fixed2V assumption.
Open R1 gives zero current/LED node0; open LED gives zero current/LED node5V.
Only DC electrical operation is accepted, not photometry or lifetime.
Isolated diode fixture:1mA,3V compliance, reverse voltage below breakdown.

### DC motor

5V CV/150mA CC supply; fuse.2Ω; MOS Ron=.1Ω at4.5V gate drive.
Faulty MOS uses1GΩ, shorted flyback diode.05Ω. Motor equations at steady state:
`Vm=I*Rw+Ke*omega`, `Kt*I=b*omega` with Rw10Ω, Kt=Ke=.05 (SI),
b=.00005N·m·s/rad. Hence effective motor resistance60Ω.
Solve the parallel short/motor network and enforce the supply current limit.
Nominal791.8rpm; diode short gives approximately52.49mV supply/150mA,
7.49mV across the motor and1.19rpm, not an arbitrary low-voltage fixture.
The model includes continuous viscous load, NOT stiction/start-up dynamics,
switching transients or fuse time-current behavior. A tiny nonzero calculated
steady speed is not a prediction that a real fan can start at that voltage.
Power tests check electrical input equals copper/MOS/fuse/short losses plus
mechanical viscous power. The MOS fixture is10mA target/1V limit at VGS4.5V.

### RC supply transient (speaker and router)

An ideal source Vs and Rs feed a current sink and a series ESR+ideal-C branch.
Let Vc be the capacitor's ideal internal voltage and I the load current:

```
Vrail = (ESR*Vs + Rs*Vc - Rs*ESR*I)/(Rs+ESR)
dVc/dt = (Vs - Rs*I - Vc)/((Rs+ESR)*C)
```

The exact exponential solution is composed over high/low phases and solved for
periodic steady state. Both sides of the instantaneous load transitions and both
endpoints are included in min/max; average and load power are integrated over a
whole period. This captures ESR jumps and finite capacitance without inventing
waveforms. ESR is treated constant in the test band; parasitic ESL, bias/temperature
dependence and controller dynamics are omitted.

Speaker: Vs5V, Rs4Ω including fuse.2Ω, C470µF/ESR.3Ω,
load20↔100mA,1kHz,50% duty. Nominal4.76V average/58.962mVpp.
Fault460µF/6.8Ω gives207.441mVpp. The load is an external specified test stimulus,
not a simulated music waveform. Buffered Vref is the supply average/2; input
100mVrms at100Hz; ideal noninverting gain1+90k/R1, with explicit rail headroom
check. The F1-associated probe measures the rail after the complete4Ω impedance,
not the tiny voltage drop directly across the fuse. No acoustics/software model.

### RLC output network (router)

Router: Vs3.3V, Rs1.35Ω+L1 DCR.15Ω, L1=10µH, C220µF/ESR.2Ω,
load20↔300mA,2kHz,10% duty. Nominal95.446mVpp, below100mVpp limit.
Unlike the RC network above, this circuit has two continuous state variables:
inductor current iL and ideal capacitor voltage Vc. It solves
`diL/dt=(Vs-(Rs+ESR)*iL-Vc+ESR*Iload)/L` and
`dVc/dt=(iL-Iload)/C`; terminal voltage is `Vc+ESR*(iL-Iload)`.
An exact2×2 real-eigenvalue matrix exponential is composed over both phases,
then the periodic fixed point is solved. The declared networks are overdamped;
unsupported oscillatory configurations are rejected rather than guessed.
Extrema include the transitions AND internal stationary points (roots of the
voltage derivative's two exponential terms). Phase integrals calculate load power.
The210µF/4.2Ω failure gives2.085V minimum and2.0375Vpp with the declared ideal
step load. Large ESR causes a terminal jump while iL and Vc remain continuous;
this is not a prediction of a particular real router's rail clamp or reboot.
The input is a distinct5V→.2Ω fuse→100Ω aggregate-load model (about249mW at
module input). At VIN≥4.5V the output equivalent is enabled; its ideal source
needs3.3V*48mA=158.4mW, below available input. Output load power is integrated
separately; the remainder includes defined equivalent losses/auxiliary consumption.
This is **not** a buck-converter netlist: L1 is linear and dynamic in the output
network, but switching control, magnetic saturation and heating are omitted.
After input or L1 open, use discharged steady
state with a disabled load, not an unphysical negative-voltage current sink.

### Clock power/reset

3.3V CV/50mA CC source, load1kΩ, C1 shunt,10kΩ reset pull-up to VCC.
C1 short.4Ω results in `.05/(1/1000+1/.4)` V, about19.992mV.
R1 open leaves RESET floating. X1's associated probe is explicitly reassigned
to buffer VCC, never a fictional1.65V crystal bias. No crystal ESR, start-up,
frequency, reset timing or timekeeping acceptance is claimed.

### LDO and sensor pull-up

Declared behavioral regulator: Vin5V, Vset3.3V, dropout.2V, Rout1Ω,
limit100mA, load100Ω. `I=min(target/(Rout+Rload),.1)`, `Vout=I*Rload`.
Normal3.2673267V. A failing regulation setting1.1V yields1.0891089V.
Output C1 short.3Ω gives29.910mV under100mA CC and approximately497mW LDO
loss. This is a short observation, NOT a safe thermal steady-state prediction.
The4.7kΩ pull-up only establishes an ideal high-impedance idle bus state;
open R1 gives floating. No digital protocol or actual LDO stability simulation.
The isolated regulator test uses the same explicitly stated100Ω reference load.

## Acceptance and tests

`tests/test_repair_shop_physics.py` checks independent KVL/KCL/torque/energy
identities, LED calibration and nonlinear behavior, LDO short and power balance,
floating inputs, amplifier gain/headroom and pause/refund migration.
The analytic RC solver is compared with an independent KCL-based RK4 integrator
over300 periods, including both sides of load transitions and mean/power integrals.
The separate RLC matrix solution is compared with an independent two-state RK4
integration over150 periods, checking state continuity, mean current, terminal
extrema, power integrals, inductor volt-second and capacitor charge balance, and
input=load+Rs/ESR losses over a period. Integral states use fourth-order quadrature
to avoid first-order/trapezoidal bias near fast ESR transients.
All17 supported faults must fail before repair and pass with either compatible
candidate. Wrong parameters/underrated parts and an injected failed model result
must fail acceptance without credits or a passing report. Existing replay,
measurement, coaching and economy tests remain in the release gate.

These tests verify the declared mathematical models, not every failure mode of
the real products. Instrument tolerance, nonideal leakage, temperature, device
spread, loop stability and OEM-specific limits require future explicit models
and validation, not additional guessed readings.

## 3D workbench

All six workbenches use the existing offline Three.js runtime with real WebGL
meshes: a drilled/extruded PCB, seated enlarged packages, metal terminals, radial
electrolytic cans, a through-hole domed LED, a five-pin LDO, fuse and crystal can.
No network/CDN, generated image or video is needed. The geometry is a teaching
location illustration and does not claim OEM package CAD, actual scale or PCB
electrical routing. The explicit equivalent network remains the circuit contract.

Raycast picks only select a test target. They cannot choose a diagnosis, perform
a measurement, buy parts or change coins. The accessible target buttons remain.
Drag/touch rotates, wheel/pinch and +/- zoom, arrows orbit, 0 or the reset button
restores the view. Camera/renderer persist across normal measurements and tool
changes; accepting a new order disposes the old GPU resources. Texture completion
redraws explicitly (including the initial green fallback), and idle scenes have
no animation loop. Missing WebGL falls back to the labeled location diagram.
Native Chrome checks require actual WebGL, all three raycast picks on all six
boards, keyboard orbit/zoom/reset, unchanged game state and phone containment.

## Primary principle references

- TI, *Understanding Basic Analog – Ideal Op Amps*, noninverting gain and ideal
  assumptions: https://www.ti.com/lit/an/slaa068b/slaa068b.pdf
- TI, *ESR, Stability, and the LDO Regulator*: actual output-capacitor ESR and
  stability depend on the regulator: https://www.ti.com/lit/an/slva115a/slva115a.pdf
- TI, *How to Debug I2C*: pull-ups, idle conditions and fault isolation:
  https://www.ti.com/lit/an/scpa063/scpa063.pdf
- University of Michigan EECS311 diode lecture (Shockley plus series resistor,
  load-line/KVL): https://eecs311.eecs.umich.edu/lec7/index.html
- University of Michigan CTMS DC motor physical model:
  https://ctms.engin.umich.edu/CTMS/index.php?example=MotorSpeed&section=SystemModeling
- Fluke, capacitance testing: power off, discharge and verify before measurement:
  https://www.fluke.com/en-us/learn/blog/digital-multimeters/how-to-measure-capacitance

References establish principles, not the invented board parameters or an OEM
endorsement. All numerical examples above are independently derived teaching
conditions and must not be copied as real-product repair instructions.
