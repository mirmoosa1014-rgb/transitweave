# Design provenance

The local reference `motion-graphic-style-library`, commit `ab7faf2be3e17350f5c6c7e78dfb53d1792ae9cc`, supplied the Blueprint visual direction: navy #071E36 paper, cyan #7FDBFF strokes, yellow #F2C14E dimensions, square edges, a faint construction grid and Helvetica-family/system-monospace typography.

The app adapts its `stroke_draw` timing (1.05 seconds, cubic-bezier 0.65, 0, 0.35, 1) to a plot trace. It omits the reference's idle blinking so measurements stay still when users inspect them. Reduced motion disables the trace animation. Plots are generated from actual server arrays, and large chart/table regions scroll locally on narrow screens. No photos, decorative fake data, soft-glass cards, perspective effects or shared dashboard template are used.

The original library's license is reproduced in `THIRD_PARTY_NOTICES.md`. Scientific figures use the same palette but ordinary Matplotlib chart layouts suited to export and reading.
