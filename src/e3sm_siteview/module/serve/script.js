// Plotly layouts adapted to the dark theme, cached so re-renders
// don't look like a layout change to trame-plotly.
const DARK_LAYOUTS = new WeakMap();

function darkLayout(layout) {
  const axis = (a) => ({
    ...a,
    gridcolor: "rgba(255, 255, 255, 0.1)",
    zerolinecolor: "rgba(255, 255, 255, 0.25)",
    linecolor: "rgba(255, 255, 255, 0.25)",
  });
  return {
    ...layout,
    paper_bgcolor: "rgba(0, 0, 0, 0)",
    plot_bgcolor: "rgba(0, 0, 0, 0)",
    font: { ...layout.font, color: "rgba(255, 255, 255, 0.87)" },
    xaxis: axis(layout.xaxis),
    yaxis: axis(layout.yaxis),
  };
}

// Plotly defaults, so exported charts look the same in light and dark theme
function exportLayout(layout) {
  const axis = (a) => ({
    ...a,
    gridcolor: "#eee",
    zerolinecolor: "#444",
    linecolor: "#444",
  });
  return {
    ...layout,
    paper_bgcolor: "white",
    plot_bgcolor: "white",
    font: { ...layout.font, color: "#444" },
    xaxis: axis(layout.xaxis),
    yaxis: axis(layout.yaxis),
  };
}

function exportName(layout, index) {
  const title = layout.title?.text || layout.yaxis?.title?.text;
  const name = String(title || `chart-${index + 1}`)
    .replace(/[^\w.-]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return `siteview-${name}`;
}

// Last focused find data formula input (variables menu inserts there)
let formulaInput = null;

function setCaret(input, pos) {
  setTimeout(() => {
    input.focus();
    input.setSelectionRange(pos, pos);
  });
}

// Keyboard shortcuts: { key: () => void } set by the KeyboardShortcuts component
let shortcuts = null;

function isEditing(target) {
  return (
    target?.isContentEditable ||
    target?.closest?.("input, textarea, select, [role='slider']")
  );
}

window.addEventListener("keydown", (event) => {
  if (!shortcuts || event.defaultPrevented) return;
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  if (isEditing(event.target)) return;
  const action = shortcuts[event.key];
  // Only time stepping auto-repeats while the key is held down
  if (!action || (event.repeat && !event.key.startsWith("Arrow"))) return;
  // Also prevents a focused button from being clicked by space
  event.preventDefault();
  action();
});

// Site map picking: lat/lon under the pointer, drag state and radius limits
const KM_PER_DEG = 111.111;
let mapDrag = null;

function mapLatLon(event, el) {
  const rect = el.getBoundingClientRect();
  const x = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
  const y = Math.min(Math.max((event.clientY - rect.top) / rect.height, 0), 1);
  const round = (v) => Math.round(v * 1000) / 1000;
  return { site_lat: round(90 - y * 180), site_lon: round(x * 360 - 180) };
}

// Coalesce drag updates to one state push per frame
function mapMoveTo(event) {
  mapDrag.next = mapLatLon(event, mapDrag.el);
  if (mapDrag.frame) return;
  mapDrag.frame = requestAnimationFrame(() => {
    if (!mapDrag) return;
    mapDrag.frame = 0;
    mapDrag.setAll(mapDrag.next);
  });
}

window.trame.utils.e3sm = {
  setShortcuts(actions) {
    shortcuts = actions;
  },
  trackFormulaInput(event) {
    formulaInput = event.target;
  },
  // Insert text at the formula cursor
  insertInFormula(formula, text) {
    formula = formula || "";
    let start = formula.length;
    let end = formula.length;
    if (formulaInput?.isConnected && formulaInput.value === formula) {
      start = formulaInput.selectionStart ?? start;
      end = formulaInput.selectionEnd ?? end;
    }
    const before = formula.slice(0, start);
    const after = formula.slice(end);
    const pre = before && !/[\s(]$/.test(before) ? " " : "";
    const post = /^[\s)]/.test(after) ? "" : " ";
    if (formulaInput?.isConnected) {
      setCaret(
        formulaInput,
        before.length + pre.length + text.length + post.length,
      );
    }
    return `${before}${pre}${text}${post}${after}`;
  },
  mapPointerDown(event, setAll) {
    if (event.button !== 0) return;
    const el = event.currentTarget;
    el.setPointerCapture(event.pointerId);
    el.classList.add("dragging");
    mapDrag = { el, setAll, frame: 0, next: null };
    mapMoveTo(event);
  },
  mapPointerMove(event) {
    if (mapDrag) mapMoveTo(event);
  },
  mapPointerUp(event) {
    if (!mapDrag) return;
    cancelAnimationFrame(mapDrag.frame);
    mapDrag.setAll(mapLatLon(event, mapDrag.el));
    mapDrag.el.classList.remove("dragging");
    mapDrag = null;
  },
  // Scroll to grow/shrink the radius, within the text field rules
  scaleRadius(radius, unit, deltaY) {
    const scale = unit === "km" ? KM_PER_DEG : 1;
    const value = (Number(radius) || 1) * Math.exp(-deltaY / 500);
    const clamped = Math.min(Math.max(value, 0.1 * scale), 89.9 * scale);
    return Number(clamped.toPrecision(3));
  },
  mapPosition(lat, lon) {
    return {
      left: `${((Number(lon) + 180) / 360) * 100}%`,
      top: `${((90 - Number(lat)) / 180) * 100}%`,
    };
  },
  // Radius circle drawn in degrees of longitude on the equirectangular map
  mapRadius(lat, lon, radius, unit, mapSize) {
    const width = mapSize?.size?.width || 0;
    const deg = (Number(radius) || 0) / (unit === "km" ? KM_PER_DEG : 1);
    const base = Math.min((deg * width) / 360, width / 4);
    const diameter = `${Math.round(Math.max(2 * base, 8))}px`;
    return {
      ...this.mapPosition(lat, lon),
      width: diameter,
      height: diameter,
    };
  },
  formatCoords(lat, lon) {
    if (lat === null || lon === null || lat === undefined || lon === undefined)
      return "";
    const ns = lat >= 0 ? "N" : "S";
    const ew = lon >= 0 ? "E" : "W";
    return `${Math.abs(lat).toFixed(3)}°${ns}, ${Math.abs(lon).toFixed(3)}°${ew}`;
  },
  match(field, query) {
    return field.name.toLowerCase()?.includes(query?.toLowerCase() || "");
  },
  // Pressure of a level index ("lev" is in hPa for EAM)
  formatLevel(levels, idx) {
    const v = levels?.[idx];
    if (v === undefined) return `level ${idx}`;
    const txt =
      v >= 100 ? v.toFixed(0) : v >= 1 ? v.toFixed(1) : v.toPrecision(2);
    return `${txt} hPa`;
  },
  // Adapt a plotly layout to the app theme
  // Download each plotly chart of a container as a png or svg file
  async exportPlots(containerId, format) {
    const charts = document.querySelectorAll(`#${containerId} .js-plotly-plot`);
    for (const [index, chart] of charts.entries()) {
      await window.Plotly.downloadImage(
        { data: chart.data, layout: exportLayout(chart.layout) },
        {
          format,
          filename: exportName(chart.layout, index),
          width: chart.clientWidth,
          height: chart.clientHeight,
          scale: format === "png" ? 3 : 1,
        },
      );
    }
  },
  plotlyLayout(layout, dark) {
    if (!dark || !layout) return layout;
    let themed = DARK_LAYOUTS.get(layout);
    if (!themed) {
      themed = darkLayout(layout);
      DARK_LAYOUTS.set(layout, themed);
    }
    return themed;
  },
};
