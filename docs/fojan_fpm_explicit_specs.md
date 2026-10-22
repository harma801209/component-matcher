# Exact FOJAN FPM specification completion

The displayed FPM253WFR300TM source identity previously had empty size, tolerance
and power fields. The strict standard-series parser rejects 300mΩ because the
published FPM standard range ends at 100mΩ, then the explicit-reference fallback
decoded only generic resistance. Its dedicated alloy identity completion covered
FRM but not FPM.

An exact FPM 25 / 3W / M or ML order code now independently exposes the coded
2512 size, nominal 6.40 x 3.20mm body, resistance, tolerance, 3W power and surface
mounting. Display normalization fills blanks only and preserves explicit data.
The actual display uses the manufacturer's metric code6432, not the generic
2512-to-6332 conversion. Selected public columns never regain internal keys.
Standard-range source records additionally expose the published 0.90mm nominal height,
-55~170°C operating range and ±50ppm/°C TCR. The source text explicitly identifies
out-of-standard resistance bands and leaves their additional limits unconfirmed.

This does not enlarge the substitute-generation envelope, alter series pricing,
infer lifecycle/stock, overwrite source records or replace runtime databases.
The advertised 500V dielectric-withstanding test must never become a maximum
working-voltage rating. A non-standard order code is not verification of every
electrical or mechanical limit of that variant.

Manufacturer-authored primary reference: FPM Low Resistance High Power Alloy
Resistor Product Specifications, FJ-JS-3001-V1.0/2025.09.24, pp.2–4; authored by
FOJAN/FOSAN and hosted by LCSC:
https://datasheet.lcsc.com/datasheet/pdf/c3359fca14918b99b0dc4539e91363e2.pdf?productCode=C7420020

Page2 ordering: 25=2512, 3W=3W, F=±1%, decimal R resistance; page3 dimensions:
2512/6432, L6.4±0.20mm W3.2±0.20mm H0.9±0.20mm; page4 standard band1–100mΩ
and large-electrode band0.5–4mΩ with published electrical limits. The nominal
package dimensions are shown separately from tolerance/detailed variant approval.

Checks: exact 300/220/330/500mΩ queries retain fields through the actual display
builder; sparse library rows are completed without overwriting known dimensions;
standard 60mΩ retains sourced limits; strict parser and substitute generation
remain bounded; no 500V working-voltage invention. Native Chrome checks the
actual rendered source tables locally and on the formal page.
