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
