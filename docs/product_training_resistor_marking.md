# Surface print on the resistor cover

Resistor exterior and internal-material modes paint value digits onto the actual
cover face. The print uses projected planar vector pixels in the cover's own
paint pass, not a screen-fixed text overlay. It follows rotation, zoom and cover
explosion and is naturally obscured by nearer faces. The resistor's initial and
reset view now looks down at the printed top, rather than up at its underside;
the other three courses retain their original default camera. Material number markers
remain separately selectable and avoid the central print region.

The page has source-scoped example rules:

- Three-character value marking for a 5% teaching example, default 102 = 1 kΩ.
- Four-character value marking for a 1% example, default 1001 = 1 kΩ.
- Stackpole RMCF/RMCP 0603 E24-only underline example: 221 = 220 Ω, 1%.
  Selecting this example also sets the lab value to 220 Ω. The maker's rule
  applies to date codes on/after 2025-04-01; shared E24/E96 values follow E96
  marking instead. The example excludes that overlap, rather than underlining
  every 1% resistor.

Read-the-print examples include 101 = 100 Ω, 4R7 = 4.7 Ω and R10 = 0.1 Ω.
Selecting a value synchronizes lab output and the visible specification value.
The existing lab resistance range now includes these sub-10Ω examples; all
electrical calculations retain their finite-positive validation. A synthetic
slider value not exactly representable in the selected rule is not rounded to
another component value or printed incorrectly.

Print conventions are not universal. Some small sizes are unmarked; precision,
power and an ordering part number must be verified separately. The marking ink
is an identification aid, not an additional resistance-producing material.
Composition and role explanations and the single-scroll embed remain unchanged
apart from this added educational content.

Sources checked:

- [Vishay surface marking guide](https://www.vishay.com/docs/20020/smdmark.pdf)
  separates three- and four-character value conventions and R decimal notation.
- [YAGEO AC specification](https://yageogroup.com/content/datasheet/asset/file/PYU-AC_E_105_ROHS_L),
  page 3, documents print above the protective coating and the AC0402 unmarked case.
- [Stackpole RMCF/RMCP specification](https://www.mouser.lt/datasheet/3/1099/1/SEI_RMCF_RMCP.pdf),
  pages 12–13, manufacturer-authored PDF distributed by Mouser, documents the
  0603 underline, date-code boundary and E24/E96 overlap exception. The direct
  manufacturer URL returned HTTP 403 during this check, so the same maker PDF
  was read from its distributor.

Verification: exact rule encoding/invalid values, cover-plane and underline
geometry, real browser mode/profile/value changes, 1440/900/390px screenshots,
rotation/explosion, other-course isolation, previous material interactions and
single host-scroll checks, plus the isolated release safety gate.
