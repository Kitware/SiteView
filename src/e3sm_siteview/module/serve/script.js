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
};
