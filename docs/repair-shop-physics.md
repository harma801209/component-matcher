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
teaching layout and does not claim OEM package CAD or actual scale. Copper now
follows the explicit equivalent network described in the routing section below.

Component/test-point raycast picks only select a test target; copper picks inspect
an entire named network. They cannot choose a diagnosis, perform
a measurement, buy parts or change coins. The accessible target buttons remain.
Drag/touch rotates, wheel/pinch and +/- zoom, arrows orbit, 0 or the reset button
restores the view. Camera/renderer persist across normal measurements and tool
changes; accepting a new order disposes the old GPU resources. The green substrate
and actual routed copper render synchronously, without a borrowed PCB texture.
Idle scenes have no
animation loop; part transfers and a powered, assembled fan request frames only
while moving, respect reduced motion, and stop when hidden/disposed.
Missing WebGL falls back to the labeled location diagram only after extraction;
before then it shows a finished-product illustration, not an x-ray PCB.
Native Chrome checks require actual WebGL, all three raycast picks on all six
boards, keyboard orbit/zoom/reset, unchanged game state and phone containment.

## Finished products and retained desk parts

New orders begin with an assembled generic lamp, fan, speaker, clock, sensor or
router. The authored low-voltage enclosure has four top-cover Phillips screws,
an unwired removable cover, a clip-in board brace and a keyed J1 cable. It is a
fictional teaching construction, not a claim about a particular OEM product.
Fixed lamp heads, motors, displays, speaker units and antennas remain on the base.

The replayable mechanical state requires power off and simulated discharge.
Each screw must be removed with the selected screwdriver before the cover can
lift; the brace is removed, J1 disconnected, and only then the board can move to
the mat. Screws remain in a tray; cover, brace, base and board remain meshes on
the same desk, with visible transfer animations and an accessible inventory.
Electrical probes, component installation and board acceptance require the
board on the mat. The bench uses the explicitly declared equivalent fixture
and load, not an imaginary functional connection to a disconnected product.

After board acceptance, power must again be off/discharged. The board is returned,
J1 reconnected, brace/cover replaced and all four screws tightened individually.
A powered assembled test recomputes the same declared electrical acceptance;
it does not certify unmodeled firmware, mechanical durability or OEM compliance.
Delivery and rewards remain blocked until this test passes.

Old in-progress saves without mechanical events migrate to the former open-board
stage without clearing purchases, coins, points or evidence. Replay reconstructs
mechanical progress from valid actions rather than trusting raw visibility flags.
Old already-paid orders cannot receive duplicate rewards.
The mechanical tests and native Chrome checks cover ordering/safety, partial
save/reload, desktop/phone layout, all six closed/opened products, and the complete
visible-controls repair-to-reassembly-to-reward loop.

## Routed teaching PCB inspection

The six explicit contact graphs in repair_shop_board.js now drive both copper
and pads. Main package contacts match the same enlarged package maps used by the
renderer (including SOT-23 G/S/D, LED/diode A/K and capacitor polarity). The custom
LDO is expressly the teaching A pin definition: 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT.
EN is tied to VIN; NC is not routed. This is not a universal SOT-23-5 pinout.

Fixed boxes labeled ideal/equivalent/test load show the rest of the declared
network: PMDC load and gate fixture, speaker Rs/feedback/Vref/amplifier, clock
load/high-impedance reset, sensor standard load/pull-up, and router RLC source/
load. They are model blocks, not secretly added replacement parts. Clock crystal
branches remain explicitly gray/unmodeled; no new crystal-fault acceptance is
implied. Source impedances are explicitly labeled equivalent, not OEM resistors.

A deterministic two-layer grid router reserves all pads/NC contacts and mounting
holes, keeps different nets apart and connects layers only with plated vias.
The scene renders visible top copper, bottom copper and (in inspection mode)
dashed blue bottom-layer projection above the substrate. A projection crossing is
not a junction; only a via joins layers. Geometry is enlarged/ideal, without trace
resistance/parasitics, manufacturing units, DRC or fabrication claims.

Board extraction defaults to a close, solid component view with transparency off.
The whole-desk view remains
available. Top view, component transparency and clickable network highlights let
players follow routes.
Transparency and the dashed bottom-layer overlay require an explicit press of
the inspection button; pressing it again restores original component materials.
Reloading/resuming and accepting/switching orders start solid, without changing
saved electrical evidence, purchases, coins or points.
Three named test points per product select the exact
existing measurement ports, not arbitrary component leads. In particular speaker
TP1 measures the RC rail after Rs, and clock TP1 measures buffered VCC rather than
a crystal terminal. Network inspection never records a measurement, answers the
diagnosis, spends coins or changes saved repair state.

Independent tests assert all six intended connection groups, exact package-pad
coordinates, absence of overlapping different-net pads, legal grid steps and
vias, every-pad copper reachability and a routed-edge flood-fill per net.
Native Chrome checks actual copper and all three test-point raycasts on each
product, GND/highlight membership, projection toggle, top view, phone bounds,
unchanged state, full repair/save/assembly/reward and original lessons.

## Hands-on instruments and progressive learning (2026-10-22)

Voltage measurements require two explicit player-placed leads on the declared
TP1–TP3/GND contacts, via actual3D picking or matching accessible buttons. Moving
a lead never measures, answers a diagnosis, spends money or reveals hidden faults.
COM is black; voltage requires the red VΩ input. Signed readings are Vred−Vblack
from the same physical solver. Reversed/differential records retain their actual
connections and are never substituted for a missing TP-to-GND report reading.
Floating/unresolved nodes remain unknown, not0V. This is an ideal infinite-input-
impedance meter; real probe loading, leakage, noise and lead resistance are absent.

The optional200mA instrument must be inserted in a declared broken SRC—LOAD supply
fixture while powered off and discharged, then powered to read. It cannot be
connected across TP/GND, removed live, retained for board acceptance, or packed
back into the enclosure. Reverse insertion changes the sign only. It is an ideal
zero-burden meter, not a model of a real fused DMM. The motor uses total source
current, the speaker uses the declared20/100mA,50%duty load average (zero with
F1open), the router uses the separate input100Ω branch, and LDO current ignoresIq.
It is not legitimate to infer input current from an unrelated output port.

Component mode explicitly docks an off/discharged isolated component in its
specified fixture (capacitance/ESR, LCR,4.5VMOS, diode or LDO as appropriate), then
returns it after reading. It does not claim a generic multimeter can measure all
those properties. Runtime mode explicitly docks the buffered diagnostic port.
Legacy saved measurement events still replay; new UI emits connection-bearing
events. Normal local economy, saved purchases, evidence and rewards are retained.

Auto guidance uses detailed actions on the first completed repair, goal-only
prompts on the second, and independent diagnosis thereafter. Players may expand a
single step or change support without penalty. The post-test report links actual
recorded observations, isolated evidence, failure reasoning, chosen specifications
and modeled verification. Unrecorded prior measurements are never fabricated.
Six optional transfer questions have no preselected answer; answers persist and
never issue additional money or points, including after delivery. This progression
is instructional support, not a validated proficiency assessment or certification.

## Held-probe visual interaction (2026-10-22)

Picking up a voltage probe now removes that lead from its previous local contact
and shows an actual lit WebGL probe/lead mesh following the mouse or pen. The tip
is ray-projected to the teaching-board plane, with a finite camera-depth fallback
for near-horizon views. The held mesh deliberately draws above packages so the
player does not lose the pointer; it is an interaction preview, not simulated
mechanical collision, soldering, force, electrical contact or hand anatomy.

Only a nearby declared TP/GND is previewed (24desktop/34touch pixels). Hover never
changes saved evidence, equations, diagnosis, coins or points. A deliberate click
uses the existing validated contact action; wrong mA input still rejects voltage
placement. Blank-area clicks do not select a component or measure. Left movement
positions the probe; right/middle drag, wheel and keyboard still control the
camera. Two-finger gestures do not attach a lead. Leaving/canceling hides the held
mesh; Escape or the accessible put-down button cancels holding. Native cursor is
hidden only while the real3D preview is visible and restored on exit, cancellation,
context loss and disposal. Accessible contact buttons remain available.

The two cached held meshes and two parked meshes reuse their geometry/materials;
moving the pointer does not allocate new geometry or textures. Wires leave the
board towards the bench rather than ending at mounting holes. No change to the
physical solver, saved event schema, current fixture or reward calculations.

### Probe direction, soft leads and phone work area

Each color has an independent, transient direction. Q/E rotates the held probe
in 15-degree steps; accessible left/right buttons also rotate connected probes
without moving their contact tips, changing readings or issuing engine events.
Black defaults towards the left bench edge and red towards the right. The cable
is a cached 40-segment tube: its initial tangent leaves the rear along the grip,
then a cubic curve reaches the bench edge. Vertex positions/normals are updated
in place. This is visual routing, not elastic, collision or cable-force physics.

Right/middle orbit keeps the held mesh and hidden native cursor stable throughout
the gesture. Snapping is suppressed during orbit and only a non-dragged primary
click can attach; the canvas suppresses its browser context menu.

At phone widths the compact next-action/tool dock sits immediately below the
260-pixel scene and a single scrolling row of view controls. It invokes the same
validated full controls, inherits their disabled state and never auto-diagnoses,
buys, measures or pays. Successful scene-affecting actions bring the scene into
view before its next animation frame. All tools and manuals remain below and
are reachable from the dock. This deliberately avoids viewport-unit/sticky
assumptions inside the production auto-height training iframe.
The trusted embed helper exposes a synchronous local height flush; mobile scene
scrolling calls it first. This prevents phase transitions (short teardown to long
electrical tools) from scrolling against the previous iframe height. The same
all-six phone test also runs against `preview_repair_shop.py`'s `/embedded` host
fixture using `--embedded`; standalone preview alone cannot catch this race.

Native Chrome checks: `tools/check_repair_shop_held_probe.py` observes visibility
during each right-drag move, exact tip pivots, tube-buffer reuse and phone turns;
`tools/check_repair_shop_mobile.py` clicks the real compact controls for all six
products, observes intermediate moving frames for eight teardown steps, checks
scene/button bounds in the top-level viewport, and tests real touch placement.

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
- Fluke, DC voltage connections, V/COM inputs and reversed DC polarity:
  https://www.fluke.com/en-ca/learn/blog/digital-multimeters/how-to-measure-dc-voltage-with-a-digital-multimeter
- Fluke15B/17B user manual, open the circuit and insert the current meter in
  series; power off/discharge before resistance/capacitance work:
  https://assets.fluke.com/manuals/15b17b__umeng0400.pdf

References establish principles, not the invented board parameters or an OEM
endorsement. All numerical examples above are independently derived teaching
conditions and must not be copied as real-product repair instructions.
