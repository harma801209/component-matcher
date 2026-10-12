# Visible MLCC inner electrodes in the existing 3D cutaway

The previous material view contained six inner electrode sheets, but their
0.025 teaching thickness and recessed front edge (z=0.275 vs ceramic z=0.3)
made them hard to see. Selecting all ceramic slabs added 1.6px outlines that
could cover the thin visible metal edges.

The existing five-part model now uses a shared exposed front cut, pale ceramic
slabs and contrasting dark-grey nickel sheets. Seven ceramic slabs sandwich six
metal sheets; thickness is deliberately enlarged for teaching. At zero explosion
the stack is contiguous, not separated by fictitious air voids. Explosion opens
the layers using the same original slider.

Each successive electrode reaches alternating copper end terminations. An
electrode stops short of the opposite termination. These connections remain
consistent as the exploded end positions move. Terminal height covers the full
stack. The material-2 marker sits on an exposed metal edge. Ceramic selection uses
a thinner outline in this model so it does not cover the electrodes.

The learner note identifies grey Ni electrodes and pale ceramic, states the
alternating end connections, and keeps the magnified/typical-structure disclaimer.
No added leader lines, duplicate diagram, libraries or business data changes.
That initial fix left exterior geometry, circuit animations, labs and quizzes unchanged.

## Follow-up: introductory/exterior view

The user's next screenshots were in exterior mode, not material mode. Its
separate old geometry still covered the stack with an opaque ceramic envelope
at 0% and its canvas label code explicitly suppressed the electrode number
below 15% explosion. Reproduction selected `electrode` at 0% and confirmed
that no `2` was painted. The first fix above did not cover that separate path.

The introductory MLCC view now reuses the same exposed material stack, mapping
it to the existing three groups: dielectric, electrode and terminal. It has no
opaque envelope concealing the teaching cut. Material mode retains five detailed
groups. Both use native, 44px numbered targets and the existing projected-anchor
separation; electrode number 2 remains present even closed, rotated or animated.
The introductory note explicitly calls this a front cutaway, not a real exposed
commercial part. Both views keep the same canvas height for MLCC. Other courses'
exterior labels and cameras are unchanged.

The electric-field overlay now uses the shared six electrode heights at all
explosion values, instead of the old ten-sheet spacing. Coloured charges and
field arrows are teaching overlays, not conductive current through the ceramic.
The PCB circuit simulation, math, labs and quizzes are untouched.

Additional validation covers exact face/ID mapping, matching exposed electrode
anchors and field heights at 0/5/10/50/100% explosion. Browser QA now explicitly
covers both modes, all three widths, closed/exploded visible bands, native marker
2 activation, marker containment and non-overlap after rotation/zoom, upper-facing
camera matching the user screenshot, animation and switching to other courses.

## Separate upper and lower ceramic covers

The outer ceramic slabs had been grouped and numbered as active dielectric. They
now have independent `upper_cover` and `lower_cover` identities, names and material
details. Five active ceramic layers separate six electrodes; the two cover regions
sit outside that active stack with no electrodes inside. Covers are drawn thicker
and light cream for teaching contrast, not as a commercial thickness specification
or a claim that their recipe/colour always differs from the active dielectric.
At 0% each cover meets the outer electrode with no artificial air void; the existing
explosion slider opens the teaching stack. End-termination height covers the body.

Both modes share those cover volumes. The introductory view keeps electrode 2
and adds covers 4/5; detailed material mode keeps its original 1-5 and adds covers
6/7. The dielectric anchor is moved from the former top slab into the active stack.
The note explicitly shows top cover -> active layers -> bottom cover, explains that
the front is cut open for teaching, and says the real cover/body is one fired piece
and electrodes are enclosed, not exposed as in the lesson. No leaders/duplicate
diagrams/extra scrolling or changes to circuit math, matching, TCR or business data.

Source: [KYOCERA AVX structure diagram, page 9](https://kyocera-avx.com/docs/techinfo/whitepapers/mlcc-tant-alternatives/AVX-Hi-CV-SMD-Capacitor-Solutions.pdf#page=9)
labels top/bottom covers separately from dielectric layers. The existing Murata
fabrication source describes the monolithic fabrication sequence. Model detail
links retain these source and material-scope boundaries.

Cover validation checks count, distinct IDs/colour/teaching thickness, outside-stack
placement, lack of electrode overlap, closed adjacency, surface anchors, body/terminal
height and consistent mode mapping. Actual-browser QA checks both native cover
buttons and their details, independent highlighting, source links, marker layout
after rotation/zoom and three widths, while retaining electrode-band checks.

## Restore a purely external MLCC view

The user clarified that the two mode buttons must not present the same cutaway.
The external mode now uses its own sealed ceramic body and two metal end caps,
with only two selectable exterior parts. No electrodes, layer lines or separately
exposed cover regions are rendered there, including after returning from a 100%
exploded internal view. It keeps camera rotation/zoom and the same canvas height.
The internal seven-part material geometry and independent covers remain unchanged.

External mode hides the dismantling slider and internal-animation button. The
existing electric-field overlay is available in capacitor material mode instead;
it is reset when switching modes and never painted over the closed external body.
Existing explosion state and lab parameters are preserved for return to material
mode. Other courses retain their existing controls and animation locations.

Verification compares the distinct actual geometry builders, validates a single
sealed ceramic volume/two overlapping end caps and exterior-only anchors, checks
an uninterrupted ceramic centre patch outside versus six visible electrode bands
inside (full-height exterior samples would also cross grey end caps), native
part selection, mode round-trip from 100% exploded state, camera/zoom, control
visibility, internal field animation, seven materials/covers and three widths.

Primary sources checked: [Murata structure FAQ](https://www.murata.com/support/faqs/capacitor/ceramiccapacitor/conf/0001)
and [Murata MLCC fabrication lesson](https://article.murata.com/en-us/article/basics-of-capacitors-3).
They describe dielectric/electrode stacking and the representative Ni internal,
Cu base and Ni/Sn plated termination structure. This teaching model does not
claim a particular commercial part's actual thickness or layer count.

Validation includes geometric adjacency, common cut plane, alternating
single-end contact/opposite-end clearance, visible electrode pixel bands in
unexploded and exploded screenshots, material selection, rotation and
1440/900/390px layouts; plus existing material interactions, single-scroll and
isolated release safety checks.
