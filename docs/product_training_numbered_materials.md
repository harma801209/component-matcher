# Numbered materials in the existing 3D view

The separate flat cross-section disclosure is removed from the training page;
the legacy renderer is no longer bundled. The same 3D canvas retains all four
courses and their 20 material parts, camera/explosion controls and source-backed
composition and role explanations.

Material mode displays numbered circular buttons near projected part anchors,
without leader lines or floating text cards. The numbers use the same source
order as the named material buttons below, and appear in the selected detail
heading. Native buttons retain descriptive accessible names, keyboard activation,
tooltips and 44px hit targets. Gentle local separation avoids collisions when
thin layers project onto nearby positions; camera movement updates positions.

The model can use the space previously reserved for floating text cards. Material
details and manufacturer links remain under the model. The single host scrollbar
still follows content expansion and contraction. No matching, member or runtime
data changes are involved.

Verification: isolated release safety gate, four-course material selection,
number/detail correspondence, camera and pointer controls, responsive screenshots
at 1440/900/390px, and the constrained native-host single-scroll regression.
