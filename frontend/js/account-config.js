// Per-site settings for the accounts UI (auth.js, history.js).
window.ARTERION_APP = {
  slug: "lv-outline",
  name: "Arterion LV Outline",
  home: "index.html",
  tasks: {
    "lv-outline": "LV outline"
  },
  // One-line summary of a saved result, shown at the top of its details.
  headline: function (r) {
    return 'LV covers ' + Math.round((r.area_fraction || 0) * 1000) / 10 + '% of the frame · confidence ' + Math.round((r.confidence || 0) * 100) + '%';
  },
};
