# PCB circuit teaching demos

The primary lesson now starts with circuit application, not internal moving dots.
`training_circuit.js` renders the same connections in PCB connection and schematic
views. The original procedural 3D meshes, parameter labs and practice tools remain.
Internal mesh animation is initially off and explicitly named internal illustration.

## Circuit boundaries

- Resistor: a 5 V source, switch, series resistor and LED return loop. A fixed 2 V
  LED drop is a classroom assumption; `I=(5-2)/R`. Compare 220 ohms vs 1 kilohm.
  Glow is qualitative, not a photometric or thermal simulation.
- Capacitor: a 3.3 V supply with a **teaching** 1 ohm supply resistance, a 10 uF
  capacitor parallel to a load changing 5 mA -> 100 mA -> 5 mA. The closed-form RC
  solution satisfies `C dV/dt=(Vs-V)/Rs-Iload`. State boundaries preserve capacitor
  voltage. Separate positive/negative capacitor lead paths never draw arrows
  across the dielectric gap. Removing the capacitor demonstrates the ideal RC
  model's immediate resistive supply droop, not a measured real-PCB transient.
  Real trace inductance, ESR/ESL, bias effects and IC behavior are not simulated.
  During discharge the blue supply contribution and orange capacitor contribution
  both pass through the IC and return via GND. Slightly offset color lanes represent
  the same shared conductors, not additional physical PCB traces. Their currents
  sum to the load current (initially 5 mA + 95 mA = 100 mA). During recharge orange
  flows only in the capacitor branch; it does not supply the IC. Steady state and
  removal of C1 disable all orange paths. No lane bridges the dielectric gap.
- Inductor: 5 V, switch, 1 mH, 10 ohm load and an ideal freewheel diode. Charging
  and release both use the exact RL exponential with preserved boundary current.
  In release, the source path is inactive; the closed path is L -> R -> ground ->
  diode -> L, with current through L in the original direction. Inductor voltage
  reverses; energy decays rather than disappearing instantaneously. This is **not
  a complete buck converter** and omits diode drop, saturation and parasitics.
- Diode: series reverse-input protection with a 1 kilohm grounded load. The
  teaching input is 0/+5/-5 V. 0.7 V is an explicitly assumed forward drop for this
  example, not a universal threshold. Reverse current is idealized to zero;
  leakage, breakdown, surge and real-part ratings still require data sheets.

These circuit values are independent of the individual-device parameter labs.
Arrow speed does not represent carrier drift, physical current rate, or wall time.
Ground is a return net, not a sink where current vanishes. PCB drawings demonstrate
connections, not manufacturable layouts.

## Controls / safety

Three selectable stages, play/pause, next, restart, and two display views.
The three media controls use icon-only 44px buttons, with native hover titles and
accessible names. Play switches to pause while running, including automatic stage
transitions; completion, course changes and reset restore play. Next is disabled at
the last stage. SVG icons are inline/decorative, with no icon-font/network dependency.
Playback ends rather than looping; it is off initially, pauses elapsed time when
offscreen or hidden, and does not mutate quiz/storage or business data. Course
changes reset circuit stages/options and stop playback through a separate event.
Live numerical metrics are not an aria-live spam stream; stage changes are announced.

## Primary references (checked 2026-10-10)

- TI, decoupling purpose and local IC supply connections:
  https://e2e.ti.com/blogs_/archives/b/precisionhub/posts/the-decoupling-capacitor-is-it-really-necessary
- Analog Devices, switching-regulator energy/freewheel discussion:
  https://www.analog.com/media/en/training-seminars/design-handbooks/power-thermal-mgmt-sect3.pdf
- TI, series diode reverse-polarity protection and forward-loss tradeoff:
  https://www.ti.com/video/5401252710001

The UI links these sources and keeps simplifying assumptions in an expandable
section. No manufacturer transient plots or proprietary PCB assets are reproduced.

## Validation

`tests/test_product_training.py`: syntax, Kirchhoff current balance, capacitor
voltage/inductor-current continuity, stored-energy decay, reverse blocking, invalid
states and integration. `tools/check_training_circuit.py [--public]`: all four
courses, flow paths and directions, capacitor comparison, both views, stage controls,
pause/resume/finish, independence from knowledge/practice tabs, and narrow layouts.
Use the normal isolated release gate and production login/data/search/BOM checks.
