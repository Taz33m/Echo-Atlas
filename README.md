<div align="center">
  <img src="./v838-monocerotis/logo.png" alt="Echo Atlas logo" width="120">
  <h1>Echo Atlas</h1>
  <p><strong>Procedural astronomy visualization inspired by V838 Monocerotis and Hubble's iconic light echo imagery.</strong></p>
  <p>
    Echo Atlas reconstructs the visual language of V838 Mon through equation-driven rendering,
    synthetic dust sheets, filament texture, asymmetric masks, and a standalone interactive console.
  </p>
  <p>
    <a href="https://youtu.be/jXmtfuEqThI">
      <img alt="Watch the Echo Atlas video on YouTube" src="https://img.shields.io/badge/Watch%20Video-YouTube-red?style=for-the-badge&logo=youtube&logoColor=white">
    </a>
  </p>
  <p>
    <a href="./v838-monocerotis/index.html"><strong>Interactive Console</strong></a>
    |
    <a href="./v838-monocerotis/render_v838.py"><strong>Python Renderer</strong></a>
    |
    <a href="./v838-monocerotis/README.md"><strong>Technical Notes</strong></a>
  </p>
  <p>
    <img alt="License: MPL-2.0" src="https://img.shields.io/badge/license-MPL--2.0-blue">
    <img alt="Python 3" src="https://img.shields.io/badge/python-3.x-3776AB?logo=python&logoColor=white">
    <img alt="Static HTML app" src="https://img.shields.io/badge/app-static%20HTML-f59e0b">
    <img alt="Procedural rendering" src="https://img.shields.io/badge/rendering-procedural-7c3aed">
    <img alt="Status" src="https://img.shields.io/badge/status-polished%20prototype-22c55e">
  </p>
</div>

![Echo Atlas banner](./v838-monocerotis/echo_atlas_banner.png)

> Echo Atlas is not a calibrated astrophysical simulation; it is a physically
> inspired procedural visualization tuned for visual recognition and
> mathematical expressiveness.

## Preview

<a href="https://youtu.be/jXmtfuEqThI">
  <img src="./v838-monocerotis/echo_atlas_preview.gif" alt="Echo Atlas epoch preview animation linking to the YouTube demo" width="100%">
</a>

Echo Atlas is not a static artwork or a photo edit. It is a procedural system
that generates V838 Mon-inspired imagery from mathematical fields, then exposes
the result through a lightweight browser interface for exploration and export.

Every image shown here is generated from the included Python renderer. No
source astronomy image is used as an input texture.

## Highlights

- **Procedural V838 Monocerotis reconstruction** using a custom Python renderer.
- **Light-echo-inspired geometry** based on moving echo surfaces through synthetic dust sheets.
- **Filamentary dust modeling** with FBM, ridge noise, radial strata, angular lace, and asymmetric gaps.
- **Interactive browser console** with epoch presets, render controls, color mapping notes, and PNG export.
- **Equation-driven color mapping** that separates warm dense dust, cool thin scattering, shadow, and star glow.
- **Reproducible outputs** with included 2002, 2004, and 2006-style generated renders.

## Why It Is Interesting

V838 Monocerotis is visually defined by a light echo: an expanding illumination
front revealing surrounding dust after the 2002 stellar outburst. Echo Atlas
turns that idea into a compact creative-coding system. The renderer combines
astronomy-inspired structure with generative art techniques, producing imagery
that feels closer to illuminated interstellar dust than to a flat glowing disk.

The project sits between computational art, scientific visualization, and
interactive software: the final image is expressive, but the pipeline behind it
is inspectable, reproducible, and tunable.

## Demo

- **Video walkthrough:** <a href="https://youtu.be/jXmtfuEqThI"><img alt="Watch the Echo Atlas video on YouTube" src="https://img.shields.io/badge/Watch%20Video-YouTube-red?style=for-the-badge&logo=youtube&logoColor=white"></a>
- **Interactive console:** open [`v838-monocerotis/index.html`](./v838-monocerotis/index.html)
- **Renderer source:** inspect [`render_v838.py`](./v838-monocerotis/render_v838.py)
- **Technical writeup:** read [`v838-monocerotis/README.md`](./v838-monocerotis/README.md)

No build step is required for the browser console. Clone the repo and open the
HTML file directly.

```sh
open v838-monocerotis/index.html
```

Render a fresh image from source:

```sh
cd v838-monocerotis
python3 -m pip install numpy pillow
python3 render_v838.py
```

## Gallery

<p align="center">
  <img src="./v838-monocerotis/v838_monocerotis_2002.png" alt="2002-style generated V838 Monocerotis render" width="32%">
  <img src="./v838-monocerotis/v838_monocerotis.png" alt="2004-style generated V838 Monocerotis render" width="32%">
  <img src="./v838-monocerotis/v838_monocerotis_2006.png" alt="2006-style generated V838 Monocerotis render" width="32%">
</p>
<p align="center"><em>2002-style early echo | 2004-style reference phase | 2006-style wide echo</em></p>

## How It Works

Each pixel is built from a layered procedural model:

```text
I(x,y) = S_star + (E_volume + E_shells) * T_dust * M_asym
```

Where:

- `S_star` is the warm central source and soft halo.
- `E_volume` approximates the light echo surface intersecting synthetic dust sheets.
- `E_shells` adds warped, broken echo-front accents.
- `T_dust` contributes filamentary texture from layered noise and trigonometric strata.
- `M_asym` breaks perfect symmetry with directional masks, clumps, and gaps.

The RGB channels are mapped separately so dense dust warms toward amber and
rust, while thinner scattering can drift toward blue-gray and cream.

## Rendering Model

The renderer is a field-composition pipeline, not an image filter. Each pixel is
evaluated from normalized coordinates, projected into a light-echo-inspired
surface model, modulated by synthetic dust, and finally mapped into RGB.

```text
coordinate field
  -> radial echo surface
  -> synthetic dust sheets
  -> filament texture
  -> asymmetry masks
  -> RGB color mapping
  -> tone mapping / export
```

The central geometric idea is an echo front moving through procedural dust
sheets:

```text
r = sqrt((x / sx)^2 + (y / sy)^2)
z_echo = (r^2 - t^2) / 2t
z_sheet_i = z_i + ax_i*x + ay_i*y + FBM_i(x,y)
E_volume = sum_i w_i * exp(-((z_echo - z_sheet_i)^2) / (2*sigma_i^2))
```

The final render combines that volume term with warped shells, filament fields,
and channel-specific color transfer:

```text
dust = ridge_noise(x,y) + radial_strata(r,theta) + angular_lace(x,y)
mask = directional(theta) * clumps(x,y) * gaps(r,theta)
I = S_star + (E_volume + E_shells) * dust * mask
RGB = tone_map(color_transfer(I, density, scatter, star_glow))
```

## Repository Structure

```text
.
|-- README.md
|-- LICENSE
`-- v838-monocerotis/
    |-- index.html                 # Standalone interactive browser console
    |-- render_v838.py             # Procedural Python renderer
    |-- logo.png                   # Echo Atlas logo
    |-- echo_atlas_banner.png      # README / social preview banner
    |-- echo_atlas_social_preview.png # 1280x640 GitHub social preview image
    |-- echo_atlas_preview.gif     # Lightweight epoch preview animation
    |-- v838_monocerotis.png       # 2004-style generated render
    |-- v838_monocerotis_2002.png  # 2002-style generated render
    |-- v838_monocerotis_2006.png  # 2006-style generated render
    `-- README.md                  # Technical documentation
```

## Scientific Scope

Echo Atlas is an artistic procedural visualization, not a calibrated
astrophysical simulation. Its structure is inspired by light echo geometry,
dust-sheet intersections, and the visual morphology of V838 Monocerotis, but it
is tuned for visual recognition, mathematical expressiveness, and interactive
exploration.

## Future Directions

- Add a hosted web build so the console launches from the repository homepage.
- Add more generated epochs and close-crop detail studies.
- Add optional debug overlays for shell fronts, dust density, and echo geometry.
- Package the renderer as a small command-line tool with preset export profiles.
