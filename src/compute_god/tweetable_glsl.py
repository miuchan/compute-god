"""Numerically reimagine a tweet-sized GLSL shader loop.

The project frequently weaves tiny creative programs into the broader
"Compute-God" mythology.  A classic example from the demoscene is the
`#つぶやきGLSL` (tweetable GLSL) challenge where artists compress entire
visual effects into a handful of characters.  The shader snippet supplied in
the task iterates a handful of trigonometric and rotation operations before
feeding the accumulated vector through ``tanh``.  Rewriting that loop in
Python gives us a deterministic, testable counterpart that can slot into other
simulation modules.

This module stays close to the original GLSL semantics while remaining
idiomatic Python.  We model the loop as :func:`iterate_shader_field`, expose a
compact :class:`ShaderInput` structure, and keep the vector algebra explicit so
that the intent remains clear during reviews.  It is intentionally lightweight
and dependency-free—``math`` provides everything we need to mirror the shader's
behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, sin, sqrt, tanh
from typing import Iterable, Tuple


Vector2 = Tuple[float, float]
Vector3 = Tuple[float, float, float]
Vector4 = Tuple[float, float, float, float]


@dataclass(frozen=True)
class ShaderInput:
    """Parameters extracted from the tweetable GLSL fragment.

    Attributes
    ----------
    time:
        Value assigned to ``t`` in the original snippet.  Controls the rotation
        angle ``T = t / 2``.
    fragment_coord:
        Two-dimensional coordinate corresponding to ``FC.xy``.  The shader
        expects these to be in clip-space where values around zero represent the
        centre of the screen.
    resolution:
        Two-dimensional resolution vector ``r.xy``.  The first component is the
        horizontal resolution, the second the vertical one.  Only the vertical
        component participates in the normalisation ``/ r.y`` but we keep both
        to stay close to the original naming.
    iterations:
        Number of iterations for the main accumulation loop.  Defaults to
        ``99`` to match ``++i < 1e2`` in GLSL.  Keeping it configurable allows
        experiments with shorter runs in tests.
    """

    time: float
    fragment_coord: Vector2
    resolution: Vector2
    iterations: int = 99

    def __post_init__(self) -> None:
        if self.iterations <= 0:
            raise ValueError("iterations must be positive")
        if self.resolution[1] == 0.0:
            raise ValueError("resolution y component must be non-zero")


def _rotate2d(point: Vector2, angle: float) -> Vector2:
    """Return ``point`` rotated by ``angle`` radians."""

    c = cos(angle)
    s = sin(angle)
    x, y = point
    return (x * c - y * s, x * s + y * c)


def _length(values: Iterable[float]) -> float:
    """Euclidean norm of the supplied vector components."""

    return sqrt(sum(component * component for component in values))


def iterate_shader_field(shader_input: ShaderInput) -> Vector4:
    """Mimic the tweetable GLSL loop and return the accumulated vector.

    The function is a faithful transliteration of the shader fragment::

        for(float i,d,s,T=t/2.;++i<1e2;){
            vec3 p=vec3((FC.xy*2.-r.xy)/r.y*d*rotate2D(T),d-4.);
            p.xz*=rotate2D(T);
            d+=s=.012+.07*abs(max(sin(length(p*p)/.4),
                                  clamp(length(p*p)-4.,.0,2.))-i/1e2);
            o+=max(1.3*sin(vec4(3,2,1,1)+i*.3)/s,-length(p*p*p));
        }
        o=tanh(o*o/2e6);

    Parameters
    ----------
    shader_input:
        Structured representation of the inputs ``t``, ``FC.xy``, ``r.xy`` and
        the iteration count.

    Returns
    -------
    tuple[float, float, float, float]
        The final value of ``o`` once normalised through the ``tanh`` step.
    """

    t = shader_input.time
    fc_x, fc_y = shader_input.fragment_coord
    res_x, res_y = shader_input.resolution

    # Match the loop initialiser ``float i, d, s, T = t / 2.``
    rotation_angle = t / 2.0
    d = 0.0
    s = 0.0
    o = (0.0, 0.0, 0.0, 0.0)

    for index in range(1, shader_input.iterations + 1):
        # ``((FC.xy * 2. - r.xy) / r.y * d) * rotate2D(T)``
        normalised = (
            (fc_x * 2.0 - res_x) / res_y * d,
            (fc_y * 2.0 - res_y) / res_y * d,
        )
        xy_rotated = _rotate2d(normalised, rotation_angle)
        p: Vector3 = (xy_rotated[0], xy_rotated[1], d - 4.0)

        # ``p.xz *= rotate2D(T);`` rotates the (x, z) components while keeping y.
        xz_rotated = _rotate2d((p[0], p[2]), rotation_angle)
        p = (xz_rotated[0], p[1], xz_rotated[1])

        p_squared = (p[0] * p[0], p[1] * p[1], p[2] * p[2])
        length_squared = _length(p_squared)

        # Equivalent to ``clamp(length(p*p) - 4., .0, 2.)``
        clamped = min(max(length_squared - 4.0, 0.0), 2.0)
        wave = sin(length_squared / 0.4)
        s = 0.012 + 0.07 * abs(max(wave, clamped) - index / 1e2)
        d += s

        p_cubed_length = _length((p_squared[0] * p[0], p_squared[1] * p[1], p_squared[2] * p[2]))
        base = (3.0, 2.0, 1.0, 1.0)
        sin_term = tuple(sin(component + index * 0.3) for component in base)
        scaled = tuple(1.3 * value / s for value in sin_term)
        threshold = -p_cubed_length
        contribution = tuple(max(value, threshold) for value in scaled)
        o = tuple(previous + current for previous, current in zip(o, contribution))

    # Final normalisation ``o = tanh(o * o / 2e6);``
    return tuple(tanh(component * component / 2_000_000.0) for component in o)


__all__ = ["ShaderInput", "iterate_shader_field"]

