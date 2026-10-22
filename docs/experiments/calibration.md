# Calibration

**Proposed; no coefficients or accuracy are measured.** Requires verified coordinate
decoding. Preserve raw evidence independently of every output transform.

1. Secure a measured grid beneath the foil. Record origin, units, orientation,
   target coordinates, and ruler/grid uncertainty. Align the puck crosshair or
   observed pen tip with targets.
2. Use at least nine widely spaced fitting points, repeated placements and stationary
   samples. Reserve separate interleaved validation points; corners alone can hide
   interior distortion. Reject degenerate/poorly distributed targets.
3. Fit least squares: `X = a*x + b*y + c`, `Y = d*x + e*y + f`. Three non-collinear
   points are the mathematical minimum. Allow reversal, rotation, scale, and shear;
   do not assume axes from a guessed packet format.
4. Report independent RMS/max Euclidean error with units, counts, and reference
   uncertainty; separately measure jitter, placement spread, edges, warm-up drift,
   and power-cycle repeatability. Counts/mm is scale, not accuracy. Host chunk rate
   is not packet rate.

Repeat for stylus, overlay side/registration, or coordinate-mode changes. Record
raw bounds, tool, serial/mode settings, reference points, coefficients, units,
residuals, valid area, and session hashes with each profile. Set the application
error tolerance before accepting calibration; do not invent factory accuracy.

Keep paper/CAD mapping (physical scale and drawing units), screen mapping (monitor,
aspect ratio), and relative pointing (lift/re-entry handling) separate. Overlay
regions use their own physical map, outside the drawing transform. Start with a
few verified CAD commands; activate on the chosen button transition, not every
position report. Unsupported historical commands remain unmapped.
