"""Settings of the 3D view"""

import plotly.colors

NAME = "viz"

# Resolution multiplier of the exported image (publication quality)
EXPORT_SCALE = 3


# 3D view colors per UI theme (background is the bottom of the gradient)
VIEW_THEMES = {
    "light": {
        "background": (0.70, 0.74, 0.78),
        "background2": (0.93, 0.95, 0.96),
        "earth": (0.67, 0.67, 0.67),
        "lines": (0.15, 0.15, 0.15),
    },
    "dark": {
        "background": (0.04, 0.07, 0.09),
        "background2": (0.15, 0.21, 0.25),
        "earth": (0.30, 0.33, 0.36),
        "lines": (0.75, 0.78, 0.80),
    },
}

EARTH_AXIS = (0, 1, 0)

# Orientation marker site cylinder (textured sphere source has radius 0.5)
SITE_MARKER_EARTH_RADIUS = 0.5
SITE_MARKER_HEIGHT = 0.1
SITE_MARKER_MIN_RADIUS = 0.03

# Selected column markers (line chart colors match its plotly traces)
COLUMN_MARKER_AREA_FRACTION = 0.05
COLUMN_MARKER_SPHERE_SCALE = 2  # sphere radius relative to cylinder radius
COLUMN_MARKER_AMBIENT = 0.5
HEATMAP_COLUMN_COLOR = (255, 255, 255)
HISTOGRAM_BINS = 200
LINE_CHART_COLORS = [
    plotly.colors.hex_to_rgb(c) for c in plotly.colors.qualitative.Plotly
]

# Find data: cells where the formula evaluates to true (1)
FIND_DATA_ARRAY = "__find_data__"

# Probe: max mouse motion (pixels) between press and release to be a click
CLICK_TOLERANCE = 3
