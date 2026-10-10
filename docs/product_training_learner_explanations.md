# Sales and assistant training copy

The PCB lesson now includes three adjacent answers: what changes in the circuit,
why the component causes the change, and what to ask a customer before selection.
Two labeled numerical comparisons update from the same stage/time as the animation.

- Resistor: 220 Ω versus 1 kΩ under the stated 5 V / 2 V LED example. The series
  current is not consumed by the resistor; electrical energy is dissipated as heat.
- Capacitor: chip voltage with/without C1 at the same time and load. The benefit is
  transient, not indefinite voltage regulation or a prediction of chip resets.
- Inductor: actual RL current versus an ideal wire replacing L1; the discharge
  example requires the existing D1 freewheel loop. No unsafe open-circuit demo.
- Diode: input versus load voltage; the example 0.7 V drop is not universal and
  actual reverse leakage/breakdown limits still matter.

Primary references remain linked inside the lesson: Vishay D/CRCW e3, TI decoupling
and reverse-polarity protection, Analog Devices power/thermal handbook Section 3.
These comparisons use the existing explicit teaching circuit equations, not
manufacturer device measurements.

Administrator/database-oriented strings have been removed. Model assumptions,
material-scope information and learning-record details remain available in closed
disclosures. Necessary selection limits remain concise and learner-facing. Learning
records continue to use the existing browser storage; no account storage was added.

Follow-up: remove implementation/model-validation prose even from disclosures.
Replace it with product-selection cautions and customer scenarios, retaining the
scientific differences and manufacturer links. Routine storage/synchronization
explanations are no longer shown; only a learner-actionable save-failure warning
appears when storage is unavailable. Progress persistence and clearing remain the
same device-local operations.

Validation: safety gate, pure cause/effect tests, rendered four-course/stage checks,
capacitor present/removed and transient comparison checks, controls, narrow layouts,
materials and existing model/quiz/practice coexistence. No runtime database changes.
