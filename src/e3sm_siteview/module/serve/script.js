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

window.trame.utils.e3sm = {
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
