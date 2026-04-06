"""generator 모듈 테스트"""

import unittest

from claudegrass.generator import (
    generate_svg,
    _calculate_thresholds,
    _token_to_color,
    _day_row,
    COLORS,
)


class TestGenerateSvg(unittest.TestCase):
    def test_empty_data(self):
        svg = generate_svg({})
        self.assertIn("<svg", svg)
        self.assertIn("</svg>", svg)
        self.assertIn("<rect", svg)

    def test_with_data(self):
        data = {
            "2026-03-26": 1000,
            "2026-03-27": 5000,
            "2026-03-28": 50000,
        }
        svg = generate_svg(data)
        self.assertIn("<svg", svg)
        self.assertIn("Less", svg)
        self.assertIn("More", svg)

    def test_contains_month_labels(self):
        svg = generate_svg({})
        # 적어도 하나의 월 라벨이 있어야 함
        has_month = any(m in svg for m in ["Jan", "Feb", "Mar", "Apr", "May",
                                            "Jun", "Jul", "Aug", "Sep", "Oct",
                                            "Nov", "Dec"])
        self.assertTrue(has_month)

    def test_tooltip_format(self):
        data = {"2026-03-26": 1234}
        svg = generate_svg(data)
        self.assertIn("1,234 tokens", svg)


class TestCalculateThresholds(unittest.TestCase):
    def test_no_data(self):
        result = _calculate_thresholds([0, 0, 0])
        self.assertEqual(len(result), 5)

    def test_single_value(self):
        result = _calculate_thresholds([0, 0, 100, 0])
        self.assertEqual(len(result), 5)

    def test_many_values(self):
        values = list(range(0, 101))
        result = _calculate_thresholds(values)
        self.assertEqual(len(result), 5)
        self.assertLessEqual(result[0], result[1])
        self.assertLessEqual(result[1], result[2])
        self.assertLessEqual(result[2], result[3])


class TestTokenToColor(unittest.TestCase):
    def test_zero_is_gray(self):
        self.assertEqual(_token_to_color(0, [10, 20, 30, 40, 50]), COLORS[0])

    def test_levels(self):
        thresholds = [100, 500, 1000, 3000, 5000]
        self.assertEqual(_token_to_color(50, thresholds), COLORS[1])
        self.assertEqual(_token_to_color(200, thresholds), COLORS[2])
        self.assertEqual(_token_to_color(800, thresholds), COLORS[3])
        self.assertEqual(_token_to_color(2000, thresholds), COLORS[4])
        self.assertEqual(_token_to_color(4000, thresholds), COLORS[5])


class TestDayRow(unittest.TestCase):
    def test_sunday_is_zero(self):
        import datetime
        # 2026-04-05 is Sunday
        d = datetime.date(2026, 4, 5)
        self.assertEqual(_day_row(d), 0)

    def test_monday_is_one(self):
        import datetime
        d = datetime.date(2026, 4, 6)
        self.assertEqual(_day_row(d), 1)

    def test_saturday_is_six(self):
        import datetime
        d = datetime.date(2026, 4, 4)
        self.assertEqual(_day_row(d), 6)


if __name__ == "__main__":
    unittest.main()
