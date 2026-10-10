# Cross-sections and material scopes

The section immediately below the original 3D/knowledge workspace adds original,
annotated 2D teaching sections. The 3D card's `剖面与材料` button jumps to it, and
the existing course-change event selects the corresponding diagram. Numbered SVG
regions and native layer buttons highlight the same selected material. Each detail
shows composition, purpose, scope and supporting source links. SVG regions support
Enter/Space; native buttons, focus and narrow-screen layouts remain accessible.

These are conceptual illustrations, not manufacturer artwork, real measured
dimensions or complete material declarations for a searched part number. Layers are
exaggerated for visibility. No proprietary fractions, purity, dopant concentration,
alloy or glass formulation is invented. Glass/metal details not specified in the
example references are expressly left to the manufacturer.

## Material examples and primary sources

- Thick film: alumina support, ruthenium-based cermet (RuO2/glass is a published
  process example), glass protection, conductive electrode and terminal finishes.
  The patent's silver pads are a process example, not a declaration for every chip.
  [Vishay construction](https://www.vishay.com/docs/60031/m.pdf),
  [published EP2286420B1 process](https://patents.google.com/patent/EP2286420B1/en),
  [Vishay D/CRCW e3 tin-on-nickel finish](https://www.vishay.com/docs/20035/dcrcwe3.pdf).
- High-permittivity MLCC: BaTiO3-based dielectric and nickel internal electrodes;
  the referenced outer termination example is Cu/Ni/Sn. Do not apply this composition
  to every C0G or other ceramic capacitor.
  [Murata material development](https://article.murata.com/en-global/article/mlcc-for-5g-smartphone-2),
  [Murata structure/material chart](https://search.murata.co.jp/Ceramy/image/img/A01X/1R0009A.pdf).
- Wound ferrite inductor: ferrite is a composite oxide, copper winding and example
  polymer wire insulation. This is not a metal-powder molded or multilayer inductor;
  its terminal alloy/finish is unspecified.
  [TDK ferrite explanation](https://www.tdk.com/en/tech-mag/ferrite02/001),
  [Coilcraft losses/shielding](https://cps.coilcraft.com/en-us/faq/),
  [wire manufacturer Elektrisola](https://update.elektrisola.com/ja/Enamelled-Wire/Info).
- Silicon PN: acceptor/donor doping within one silicon crystal; depletion is not a
  foreign inserted layer. P/N is unfolded laterally for teaching, not the real
  planar-diffusion geometry of 1N4148. Glass package and leads do not identify an
  exact recipe or semiconductor type.
  [BYU cleanroom silicon doping](https://www.cleanroom.byu.edu/EW_wafer_specs),
  [Nexperia package/planar description](https://www.nexperia.com/product/1N4148),
  [Toshiba PN/depletion explanation](https://toshiba.semicon-storage.com/us/semiconductor/knowledge/e-learning/discrete/chap1/chap1-6.html).

Sources checked 2026-10-10; page-level sources and notes identify each example's
limits. The two added gate tests cover schema/source/unique layer IDs, scope warnings,
frozen data, inline loading and no persistence. `tools/check_training_materials.py
[--public]` checks four courses, all layer details, SVG keyboard/click, entry focus,
links, coexistence with existing tools and 1440/900/390px captures. The ordinary
training circuit regression still verifies its media controls and current paths.
No catalog, search/matching, member/cost/report database or stored quiz logic changes.
