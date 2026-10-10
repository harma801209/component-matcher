# Shared 3D internal-material mode

The existing canvas now has `外观结构` and `内部材料结构` modes. Material mode uses
procedural cutaway/exploded volumes for all four courses, including 20 material
parts. Every callout has a structure name, material summary and a projected leader
to its mesh location. Native callout buttons, mesh clicks and the part strip select
the same component; composition, role, product differences and primary-source
links appear in the same model card.

`training_material_data.js` is the single immutable source of lesson/material data;
both the existing reference section and the new 3D view use it. The 2D reference
is collapsed by default. Its selection synchronizes with the 3D material selection
when material mode is active. The old jump button now toggles the same canvas.

Camera/zoom and experiment parameters survive mode switches. Course switching
retains the chosen mode while using the original per-course parameter reset.
Rotation, wheel/pinch zoom, keyboard navigation and explosion share the existing
camera and controls. Internal principle animation remains available in exterior
mode; it is disabled in material mode so exterior animation paths are not drawn
on incompatible material geometry. Circuit animations/labs/quizzes are unchanged.

Resistor terminal layers and MLCC electrodes/terminal stacks are visually enlarged.
The inductor includes an explicitly enlarged enamel/copper sample next to its
winding. PN regions remain adjacent in the same silicon chip during explosion;
the junction is a region, not an inserted metal or insulating sheet. Material
composition and source boundaries are unchanged from the verified lessons. No
claim of one manufacturer's exact internal fabrication geometry is introduced.

Checks cover finite geometry/part IDs/anchors, same-canvas mode changes, all 20
selections, source synchronization, projected leaders after rotation, mouse mesh
picking/drag/wheel, keyboard zoom, auto-rotation/reset, course changes within
material mode, invalid requests, 1440/900/390 layouts and original training paths.
No additional asset downloads, libraries, storage or runtime-database writes.
