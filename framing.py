"""Encuadre por ajuste de bounding box: garantiza que el plano cabe en el area segura."""
import numpy as np
from engine import norm, look_at


def project(pts, eye, target, fov, W, H):
    R, t = look_at(eye, target)
    A = np.asarray(pts, float)
    P = A @ R.T + t
    z = P[:, 2]
    focal = (W * 0.5) / np.tan(np.radians(fov) * 0.5)
    ok = z > 0.2
    sx = np.where(ok, P[:, 0] / np.maximum(z, 1e-6) * focal + W * 0.5, -1e9) / W
    sy = np.where(ok, -P[:, 1] / np.maximum(z, 1e-6) * focal + H * 0.5, -1e9) / H
    return sx, sy, z


def fits(pts, eye, target, fov, W, H, safe=(0.05, 0.95, 0.08, 0.92)):
    sx, sy, z = project(pts, eye, target, fov, W, H)
    if (z <= 0.2).any():
        return False
    return (sx.min() > safe[0] and sx.max() < safe[1] and sy.min() > safe[2] and sy.max() < safe[3])


def fit_view(points, center, direction, fov, W, H, safe=(0.05, 0.95, 0.08, 0.92),
             dmin=3.0, dmax=90.0, n=90):
    """devuelve (eye, target) que encuadra `points` con margen dentro del area segura"""
    pts = np.asarray(points, float)
    center = np.asarray(center, float)
    u = norm(np.asarray(direction, float))
    best = None
    for d in np.linspace(dmax, dmin, n):
        eye = center + u * d
        if fits(pts, eye, center, fov, W, H, safe):
            best = eye
        else:
            break
    if best is None:
        best = center + u * dmax
    return best, center
