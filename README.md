# Echo Atlas

**Echo Atlas** is a procedural astronomy visualization project inspired by
V838 Monocerotis and the famous Hubble light echo imagery that followed its
2002 outburst.

The project recreates the recognizable visual language of V838 Mon through a
math-driven renderer and standalone browser console. It focuses on light echo
geometry, synthetic dust sheets, filament texture, asymmetric masks, and
equation-driven color mapping.

![Echo Atlas render](./v838-monocerotis/v838_monocerotis.png)

## Demo

[Watch the Echo Atlas demo video](https://youtu.be/jXmtfuEqThI)

## Project

The full app, renderer, generated images, and documentation live in:

[`v838-monocerotis/`](./v838-monocerotis/)

Open the interactive console directly:

```sh
open v838-monocerotis/index.html
```

Render from source:

```sh
cd v838-monocerotis
python3 -m pip install numpy pillow
python3 render_v838.py
```

## Scientific Scope

Echo Atlas is an artistic procedural visualization, not a calibrated
astrophysical simulation. It is physically inspired in its use of light echo
geometry and dust-sheet intersections, but tuned for visual recognition and
mathematical expressiveness.
