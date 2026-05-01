#!/usr/bin/env python3
"""Procedural V838 Monocerotis light echo renderer.

Target: a structurally inspired Hubble-style V838 Mon light echo, not an
accretion disk or a literal copy of one frame. The image is built from layers:
warm central source, soft halo, warped echo shells, filamentary dust density,
asymmetric gaps, and a color map that separates rusty dense dust from cooler
thin scattering.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


EPOCH_PHASES = {
    "2002": 0.28,
    "2004": 0.58,
    "2006": 0.82,
}


def clamp01(value: np.ndarray) -> np.ndarray:
    return np.clip(value, 0.0, 1.0)


def smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    t = clamp01((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def fract(value: np.ndarray) -> np.ndarray:
    return value - np.floor(value)


def hash2(x: np.ndarray, y: np.ndarray, seed: float) -> np.ndarray:
    return fract(np.sin(x * 127.1 + y * 311.7 + seed * 74.7) * 43758.5453123)


def value_noise(x: np.ndarray, y: np.ndarray, seed: float) -> np.ndarray:
    xi = np.floor(x)
    yi = np.floor(y)
    xf = x - xi
    yf = y - yi
    u = xf * xf * (3.0 - 2.0 * xf)
    v = yf * yf * (3.0 - 2.0 * yf)

    a = hash2(xi, yi, seed)
    b = hash2(xi + 1.0, yi, seed)
    c = hash2(xi, yi + 1.0, seed)
    d = hash2(xi + 1.0, yi + 1.0, seed)

    return (a * (1.0 - u) + b * u) * (1.0 - v) + (c * (1.0 - u) + d * u) * v


def fbm(x: np.ndarray, y: np.ndarray, seed: float, octaves: int = 5) -> np.ndarray:
    total = np.zeros_like(x)
    amp = 0.5
    freq = 1.0
    norm = 0.0
    for octave in range(octaves):
        total += amp * value_noise(x * freq, y * freq, seed + octave * 17.13)
        norm += amp
        freq *= 2.03
        amp *= 0.52
    return total / norm


def ridge_noise(x: np.ndarray, y: np.ndarray, seed: float, octaves: int = 4) -> np.ndarray:
    n = fbm(x, y, seed, octaves)
    return (1.0 - np.abs(2.0 * n - 1.0)) ** 1.7


def angle_delta(theta: np.ndarray, center: float) -> np.ndarray:
    return np.arctan2(np.sin(theta - center), np.cos(theta - center))


def render(width: int, height: int, phase: float, seed: float) -> Image.Image:
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)

    # Star-centered coordinate system. V838 Mon's signature is a light echo
    # through dust, so the star is kept small and warm while the surrounding
    # scattering surfaces carry most of the visual complexity.
    sx0 = -0.03
    sy0 = 0.02
    x = (xx / width - 0.5) * 2.54 - sx0
    y = (yy / height - 0.5) * 1.82 - sy0
    x += 0.018 * np.sin(yy / height * np.pi)

    theta = np.arctan2(y * 1.02, x)
    r_base = np.sqrt((x / 1.03) ** 2 + (y / 0.96) ** 2)

    low = fbm(x * 1.35 + phase * 0.8, y * 1.35 - phase * 0.5, seed + 1.0, 5)
    medium = fbm(x * 3.1 - phase * 0.6, y * 3.1 + phase * 0.9, seed + 9.0, 5)
    fine = ridge_noise(x * 9.0 + 0.6, y * 9.0 - 0.4, seed + 17.0, 4)
    echo_extent = 0.72 + 0.48 * phase

    boundary = (
        0.84
        + 0.14 * np.sin(theta - 0.55)
        + 0.11 * np.sin(2.0 * theta + 1.65)
        - 0.080 * np.cos(3.0 * theta - 0.6)
        + 0.05 * np.sin(6.0 * theta + 1.1)
        + 0.14 * (low - 0.5)
    )
    boundary += 0.12 * np.exp(-(angle_delta(theta, -2.45) / 0.58) ** 2)
    boundary -= 0.13 * np.exp(-(angle_delta(theta, 0.15) / 0.42) ** 2)
    boundary += 0.06 * np.exp(-(angle_delta(theta, 1.85) / 0.35) ** 2)
    boundary *= echo_extent

    cloud = smoothstep(boundary + 0.16, boundary - 0.05, r_base)
    cloud *= smoothstep(0.11, 0.24, r_base)

    # Low-frequency masks make the echo incomplete instead of target-like.
    sector = (
        0.68
        + 0.27 * np.cos(theta + 2.35)
        + 0.22 * np.sin(2.0 * theta - 0.35)
        + 0.15 * np.cos(5.0 * theta + 1.5)
    )
    gaps = 1.0
    gaps -= 0.58 * np.exp(-(angle_delta(theta, 0.45) / 0.24) ** 2) * smoothstep(0.32, 0.74, r_base)
    gaps -= 0.46 * np.exp(-(angle_delta(theta, -1.10) / 0.30) ** 2) * smoothstep(0.38, 0.88, r_base)
    gaps -= 0.40 * np.exp(-(angle_delta(theta, 2.15) / 0.26) ** 2) * smoothstep(0.28, 0.78, r_base)
    gaps -= 0.32 * np.exp(-(angle_delta(theta, -0.18) / 0.18) ** 2) * smoothstep(0.50, 0.95, r_base)
    clump_mask = smoothstep(0.28, 0.82, fbm(x * 2.2 + 4.0, y * 2.2 - 1.5, seed + 27.0, 5))
    asymmetry = clamp01(sector * gaps * (0.42 + 0.82 * clump_mask))

    shells = np.zeros_like(x)
    shell_density = np.zeros_like(x)
    cool_scatter = np.zeros_like(x)
    warm_scatter = np.zeros_like(x)
    shell_specs = (
        (0.19, 0.020, 0.42, -0.010, 0.010, 4.0, 0.2),
        (0.29, 0.024, 0.52, 0.016, -0.006, 5.0, 1.4),
        (0.40, 0.025, 0.66, -0.014, -0.020, 3.0, 2.6),
        (0.52, 0.030, 0.92, 0.020, 0.018, 6.0, 0.9),
        (0.64, 0.033, 1.00, -0.030, 0.014, 4.0, 2.1),
        (0.76, 0.038, 0.88, 0.028, -0.016, 7.0, 1.7),
        (0.90, 0.050, 0.78, -0.018, 0.026, 5.0, 3.0),
    )

    for index, (radius, width_i, weight, cx, cy, harmonic, offset) in enumerate(shell_specs):
        radius *= echo_extent
        width_i *= 0.88 + 0.16 * echo_extent
        xi = x - cx
        yi = y - cy
        ti = np.arctan2(yi * (1.0 + 0.035 * np.sin(offset)), xi)
        ri = np.sqrt((xi / (1.02 + 0.035 * np.cos(offset))) ** 2 + (yi / (0.95 + 0.025 * np.sin(offset))) ** 2)
        warp = (
            0.028 * np.sin(harmonic * ti + offset + phase * 1.4)
            + 0.018 * np.sin((harmonic + 2.0) * ti - 1.7 * offset)
            + 0.040 * (fbm(xi * 2.0 + index, yi * 2.0 - index, seed + index * 11.0, 4) - 0.5)
        )
        band = np.exp(-((ri + warp - radius) ** 2) / (2.0 * width_i**2))
        arc_breaks = smoothstep(
            0.34,
            0.82,
            fbm(
                np.cos(ti) * (2.1 + 0.17 * index) + phase,
                np.sin(ti) * (2.1 + 0.17 * index) - phase,
                seed + 70.0 + index,
                4,
            ),
        )
        directional = 0.60 + 0.40 * np.cos(ti - 0.35 - 0.18 * index)
        shell = weight * band * (0.24 + 0.94 * arc_breaks) * (0.55 + 0.62 * directional)
        shells += shell
        shell_density += shell * (1.18 - 0.56 * radius)
        cool_scatter += shell * smoothstep(0.48, 0.96, radius)
        warm_scatter += shell * smoothstep(0.78, 0.20, radius)

    # A light echo is closer to a moving slice through 3D dust than a stack of
    # flat rings. This synthetic paraboloid/sheet intersection supplies the
    # main cloud-like structure; the radial shells above are only accents.
    echo_time = 0.45 + 0.58 * phase
    z_echo = (r_base**2 - echo_time**2) / (2.0 * echo_time)
    volume_echo = np.zeros_like(x)
    volume_density = np.zeros_like(x)
    cool_volume = np.zeros_like(x)
    warm_volume = np.zeros_like(x)
    sheet_specs = (
        (-0.34, 0.055, 0.74, 0.16, -0.08, 1.8, 0.3),
        (-0.18, 0.045, 0.86, -0.08, 0.18, 2.4, 1.7),
        (0.02, 0.052, 1.00, 0.10, 0.06, 3.1, 2.4),
        (0.21, 0.060, 0.72, -0.15, -0.02, 2.7, 3.6),
        (0.40, 0.076, 0.54, 0.03, -0.16, 1.5, 4.8),
    )
    for index, (z0, thickness, weight, tilt_x, tilt_y, freq, offset) in enumerate(sheet_specs):
        sheet_noise = fbm(
            x * freq + offset + phase,
            y * freq - offset * 0.7,
            seed + 120.0 + index,
            5,
        )
        sheet_z = (
            z0
            + tilt_x * x
            + tilt_y * y
            + 0.16 * (sheet_noise - 0.5)
            + 0.035 * np.sin((2.0 + 0.4 * index) * theta + offset)
        )
        front = np.exp(-((z_echo - sheet_z) ** 2) / (2.0 * thickness**2))
        sheet_dust = smoothstep(
            0.24,
            0.84,
            fbm(x * (2.7 + 0.25 * index) + offset, y * (2.7 + 0.25 * index) - offset, seed + 150.0 + index, 5),
        )
        sheet_dust *= 0.45 + 0.70 * ridge_noise(
            x * (5.6 + index),
            y * (5.6 + index),
            seed + 170.0 + index,
            4,
        )
        edge_fade = smoothstep(boundary + 0.20, boundary - 0.10, r_base) * smoothstep(0.09, 0.20, r_base)
        directional = 0.62 + 0.38 * np.cos(theta - 0.45 + 0.35 * index)
        contribution = weight * front * sheet_dust * edge_fade * directional
        volume_echo += contribution
        volume_density += contribution * (0.52 + 0.72 * sheet_dust)
        cool_volume += contribution * smoothstep(0.44, 0.95, r_base)
        warm_volume += contribution * smoothstep(0.82, 0.16, r_base)

    radial_strata = (
        0.5
        + 0.5
        * np.sin(
            58.0 * (r_base + 0.020 * np.sin(5.0 * theta) + 0.030 * (low - 0.5))
            + 5.0 * np.sin(3.0 * theta + phase)
        )
    )
    angular_lace = (
        0.5
        + 0.5
        * np.sin(
            22.0 * (x * np.cos(1.05) + y * np.sin(1.05))
            + 10.0 * medium
            + 4.0 * np.sin(theta - 0.7)
        )
    )
    filaments = 0.70 * radial_strata**5 + 0.48 * angular_lace**4 + 0.65 * fine
    filaments = clamp01(filaments)

    translucent_dust = cloud * (0.11 + 0.48 * medium + 0.34 * fine) * (0.50 + 0.70 * clump_mask)
    illuminated_dust = (
        volume_echo * (0.52 + 0.86 * filaments)
        + 0.34 * shells * (0.26 + 0.82 * filaments)
        + 0.14 * translucent_dust
    ) * asymmetry

    # Darker lanes and voids give the projected cloud a 3D folded-shell feel.
    lane_a = np.exp(-(angle_delta(theta, 0.15) / 0.19) ** 2) * smoothstep(0.32, 0.76, r_base)
    lane_b = np.exp(-(angle_delta(theta, -2.55) / 0.23) ** 2) * smoothstep(0.40, 0.92, r_base)
    lane_c = np.exp(-((r_base - (0.54 + 0.06 * np.sin(2.2 * theta))) ** 2) / (2.0 * 0.020**2))
    voids = 0.60 * lane_a + 0.44 * lane_b + 0.30 * lane_c * smoothstep(0.40, 0.76, medium)
    illuminated_dust *= clamp01(1.0 - voids)

    # Central source: warm and present, but intentionally not a white-hot disk.
    rho = np.sqrt((x + sx0) ** 2 + (y + sy0) ** 2)
    star_core = np.exp(-(rho / 0.012) ** 2)
    star_glow = np.exp(-(rho / 0.070) ** 2)
    inner_halo = np.exp(-(rho / 0.16) ** 2) * (0.72 + 0.28 * medium)
    star = star_core + 0.55 * star_glow + 0.13 * inner_halo

    vignette = clamp01(1.08 - 0.40 * np.sqrt((x * 0.82) ** 2 + (y * 0.98) ** 2))
    background_noise = fbm(x * 1.0 + 8.0, y * 1.0 - 2.0, seed + 200.0, 4)
    image = np.zeros((height, width, 3), dtype=np.float32)
    image[..., 0] = (0.012 + 0.020 * background_noise) * vignette
    image[..., 1] = (0.016 + 0.020 * background_noise) * vignette
    image[..., 2] = (0.032 + 0.050 * background_noise) * vignette

    density = clamp01(0.28 * shell_density + 0.78 * volume_density + 0.54 * translucent_dust)
    thin = clamp01(0.55 * cool_scatter + 1.35 * cool_volume + (1.0 - density) * illuminated_dust * 0.32)
    inner = clamp01(0.55 * warm_scatter + 1.30 * warm_volume)
    shadow = clamp01(voids + (1.0 - clump_mask) * cloud * 0.38)

    red = illuminated_dust * (0.98 + 0.95 * density + 0.56 * inner) + 0.14 * translucent_dust
    green = illuminated_dust * (0.62 + 0.34 * thin + 0.18 * density) + 0.13 * translucent_dust
    blue = illuminated_dust * (0.36 + 0.82 * thin - 0.26 * density) + 0.15 * translucent_dust

    image[..., 0] += red * (1.0 - 0.10 * shadow)
    image[..., 1] += green * (1.0 - 0.24 * shadow)
    image[..., 2] += blue * (1.0 - 0.30 * shadow)

    image[..., 0] += 2.00 * star_core + 0.56 * star_glow + 0.09 * inner_halo
    image[..., 1] += 1.05 * star_core + 0.29 * star_glow + 0.06 * inner_halo
    image[..., 2] += 0.54 * star_core + 0.13 * star_glow + 0.04 * inner_halo

    # Sparse background stars are kept behind the dusty echo.
    cell = 0.021
    gx = np.floor((x + 2.0) / cell)
    gy = np.floor((y + 2.0) / cell)
    local_x = fract((x + 2.0) / cell) - 0.5
    local_y = fract((y + 2.0) / cell) - 0.5
    star_hash = hash2(gx, gy, seed + 500.0)
    points = np.exp(-(local_x**2 + local_y**2) / 0.012) * (star_hash > 0.9975)
    points *= hash2(gx - 4.0, gy + 8.0, seed + 501.0) * (1.0 - clamp01(cloud + 0.6 * shells))
    image[..., 0] += 0.55 * points
    image[..., 1] += 0.64 * points
    image[..., 2] += 0.85 * points

    image *= vignette[..., None] * 1.03
    image = 1.0 - np.exp(-1.22 * image)
    image = clamp01(image ** (1.0 / 2.10))

    return Image.fromarray((image * 255.0).astype(np.uint8), mode="RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render procedural V838 Monocerotis light echo art.")
    parser.add_argument("--width", type=int, default=2000)
    parser.add_argument("--height", type=int, default=960)
    parser.add_argument("--epoch", choices=sorted(EPOCH_PHASES), default="2004")
    parser.add_argument("--phase", type=float, default=None, help="Override the selected epoch phase.")
    parser.add_argument("--seed", type=float, default=838.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("v838_monocerotis.png"),
    )
    args = parser.parse_args()

    phase = EPOCH_PHASES[args.epoch] if args.phase is None else args.phase
    image = render(args.width, args.height, phase, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(f"Wrote {args.output} ({args.width}x{args.height})")


if __name__ == "__main__":
    main()
