# Milliohm OCR and matching boundaries

## Reproductions

- `HoLLR25 1 2-3W-2m R- 1 %`, `Milliohm(毫欧)`, `2mQ2,±1 %,3W`
  previously became 2MΩ and lost2512. It now retains2mΩ=.002Ω,2512,1%,3W.
- `HoJ LR251 2-3W-500mR- 1%`, `Milliohm(毫欧)`, `500mΩ,±1 %,3W`
  retains500mΩ=.5Ω,2512,1%,3W. Original manufacturer identity is not
  silently changed (no inserted D, no J-to-L replacement).

The OCR normalizer repairs only standalone numeric units before tolerance
markers, and split lower-case milli units before their explicit ohm marker.
Bare lowercase m is incomplete, not a mega-ohm suffix. BOM result keys retain
the milli/mega distinction. Same-image match signatures advance to version5.

For these structured descriptions the BOM evaluates the model-description,
independent specification and brand together before accepting a reduced-field
match. Conflicting explicit resistance values stop matching. Truncated HOLLR25
tokens are not independent model-rule evidence for consistency warnings.

## Source boundary, not an enlarged catalogue

2mΩ/2512/3W returns the existing source-bounded FPM M/ML candidates. ML is a
large-electrode version and needs pad confirmation when the source description
does not establish electrode geometry.

500mΩ/2512/3W must not be synthesized as FPM253WFR500TM. The public commercial
identity clue FPM253WFR500TN is shown as **pending manufacturer confirmation**,
outside matched results and without inferred pricing. Exact N references can
show encoded2512/3W/resistance/tolerance but remain unverified for substitution;
they cannot borrow M series prices. Exact imported costs are not overwritten.

Primary manufacturer-authored reference, reviewed page1 ordering and page3
electrical table: FOJAN/FOSAN FPM FJ-JS-3004-V1.0/2024.03.27:
https://atta.szlcsc.com/upload/public/pdf/source/20250318/C5F122670D95A5962CFB97BFCB71D97F.pdf

- Ordering gives25=2512,3W=3W,F=1%,R500=500mΩ,N=NiCu.
- Standard electrical table gives2512/2W2–680mΩ,2512/3W2–100mΩ,
  large-electrode2512-L/3W1–4mΩ. The2W row cannot approve3W/500mΩ.
- A newer M-material reference (seefojan_fpm_explicit_specs.md) gives3W1–100mΩ
  and ML.5–4mΩ. Do not combine these tables to invent a3W/500mΩ envelope.
- The500V dielectric test is not maximum working voltage.
- Nonstandard requirements require the supplier's dedicated approval.

Commercial identity clue only (not primary technical approval):
https://item.szlcsc.com/48791831.html

This patch does not add unverified catalogue members, infer production state,
alter price lists or touch member/cost/report runtime databases. Raw source text
is retained for review. Text and mapped-column integration acceptance do not
constitute a successful end-to-end original-image OCR upload test.
