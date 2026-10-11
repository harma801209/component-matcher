# Training uses one page-level vertical scrollbar

The previous training iframe was fixed at 1050px with internal scrolling enabled;
its content was about 2370px at the inspected desktop size. The Streamlit page
also scrolls, so users encountered two separate vertical scroll areas.

Only the training embed now sets `scrolling=False`. The new inline
`training_embed.js` sizes its own same-origin frame to the training root's natural
bounding height plus a small rounding allowance. It releases the closest native
element container's fixed height and fixed flex basis, scoped to that frame, and follows ResizeObserver,
font/load, resize and disclosure changes. Content expansion and contraction both
work; document scrollHeight is deliberately not used as the content measurement
because it can be floored by the viewport and retain blank space after shrinking.

Standalone lessons keep normal document scrolling. Other embedded tables/BOM
previews are unaffected. Canvas wheel zoom remains intentional; ordinary page
wheel scrolling uses the host page. No database, storage, dependency or backend
matching changes are involved.

The official [HTML embed reference](https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v1.html)
documents that disabling scrolling alone crops over-height content, hence the
height update is required rather than simply hiding a scrollbar.

Verification covers same-origin constrained-host fixtures and the actual formal
Streamlit container: no training overflow/cropping, outer-page wheel and bottom
reachability, mode/course/tab changes, expanding/collapsing references, narrow
layouts, stable height without growth loops and unrelated iframe height isolation.

The formal native container also had `flex: 0 0 1050px`; height:auto alone did not
release that layout constraint. The constrained-host regression fixture reproduces
that flex layout, and the fix explicitly uses a content-sized flex basis on this
one container. Parent and child rectangles must agree in the browser check.
