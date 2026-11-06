"""Independent geometry checks for the bounded placement contract."""

import math
import unittest

from verified_pipeline.placement import (
    bounds_report, diameter_for_height, place_in_sphere_and_cube,
    projected_cube_bounds_px, projected_sphere_height_px,
)


class PlacementGeometryTests(unittest.TestCase):
    def test_target_heights_against_numeric_tangent_search(self):
        # Ray slopes at tangent are stationary values of y/z over the circle.
        distance = 1.58
        focal = 960 / (2 * math.tan(math.radians(30)))
        for target in (50, 70, 90):
            diameter = diameter_for_height(target, distance, 60, 960, 540)
            radius = diameter / 2
            samples = [radius * math.sin(2 * math.pi * i / 200000)
                       / (distance + radius * math.cos(2 * math.pi * i / 200000))
                       for i in range(200000)]
            sampled_height = focal * (max(samples) - min(samples))
            self.assertAlmostEqual(sampled_height, target * 5.4, places=6)
            self.assertAlmostEqual(projected_sphere_height_px(diameter, distance, 60, 960),
                                   target * 5.4, places=9)

    def test_shared_fit_contains_mesh_and_cube(self):
        vertices = [(2, 4, 6), (-1, 3, 5), (1, -2, 8), (0, 0, 1)]
        for target in (50, 70, 90):
            p = place_in_sphere_and_cube(vertices, target, 1.58, 60, 960, 540)
            self.assertEqual(p.sphere_diameter_m, p.cube_edge_m)
            self.assertAlmostEqual(p.projected_sphere_height_px / 540 * 100, target)
            for vertex in vertices:
                out = p.transform(vertex)
                self.assertLessEqual(math.dist(out, (0, 0, 0)), p.sphere_diameter_m / 2 + 1e-12)
                self.assertTrue(all(abs(x) <= p.cube_edge_m / 2 + 1e-12 for x in out))

    def test_cube_projection_reports_overflow_without_resizing(self):
        identity = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        d = diameter_for_height(90, 1.58, 60, 960, 540)
        bounds = projected_cube_bounds_px(d, 1.58, 60, 960, 540, identity)
        report = bounds_report(bounds, 960, 540)
        self.assertGreater(report["height_percent"], 90)
        self.assertEqual(d, diameter_for_height(90, 1.58, 60, 960, 540))

    def test_rejects_invalid_mesh_and_camera(self):
        with self.assertRaises(ValueError):
            place_in_sphere_and_cube([], 70, 1.58, 60, 960, 540)
        with self.assertRaises(ValueError):
            place_in_sphere_and_cube([(0, 0, 0)], 70, 1.58, 60, 960, 540)
        with self.assertRaises(ValueError):
            diameter_for_height(70, 0, 60, 960, 540)
        with self.assertRaises(ValueError):
            projected_cube_bounds_px(1, 1.58, 60, 960, 540,
                                     ((2, 0, 0), (0, 1, 0), (0, 0, 1)))


if __name__ == "__main__":
    unittest.main()
