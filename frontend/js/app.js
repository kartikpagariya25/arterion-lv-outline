(() => {
  const $ = (id) => document.getElementById(id);
  const API = window.API_BASE.replace(/\/$/, "");
  const show = (el, on) => (el.hidden = !on);
  let src = "image";
  let current = null;

  /* ---------- status (retries until the API answers) ---------- */
  async function ping() {
    const el = $("status");
    try {
      if (!(await fetch(API + "/health", { cache: "no-store" })).ok) throw 0;
      el.className = "status ok"; el.lastElementChild.textContent = "api online";
    } catch {
      el.className = "status bad"; el.lastElementChild.textContent = "api offline · " + API;
      setTimeout(ping, 4000);
    }
  }
  ping();

  /* ---------- source tabs ---------- */
  document.querySelectorAll(".tabs>[data-src]").forEach((b) => b.addEventListener("click", () => {
    src = b.dataset.src;
    document.querySelectorAll(".tabs>[data-src]").forEach((x) => { x.classList.toggle("on", x === b); x.setAttribute("aria-selected", x === b); });
    if (current) return;
    showSource();
  }));
  function showSource() {
    show($("drop"), src === "image");
    show($("vidpick"), src === "video");
    if (src === "video" && !$("video").getAttribute("src")) {
      show($("vidpick"), false); show($("drop"), true);
      $("file").accept = "video/*"; $("dropTitle").textContent = "Drop an echo video"; $("dropHint").textContent = "MP4 or WebM · then scrub to a frame";
    } else {
      $("file").accept = src === "video" ? "video/*" : "image/*";
      $("dropTitle").textContent = src === "video" ? "Drop an echo video" : "Drop an echo frame";
      $("dropHint").textContent = src === "video" ? "MP4 or WebM · then scrub to a frame" : "PNG or JPG · click to browse";
    }
  }

  /* ---------- input ---------- */
  const drop = $("drop");
  ["dragenter", "dragover"].forEach((e) => drop.addEventListener(e, (ev) => { ev.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((e) => drop.addEventListener(e, (ev) => { ev.preventDefault(); drop.classList.remove("over"); }));
  drop.addEventListener("drop", (e) => e.dataTransfer.files[0] && onFile(e.dataTransfer.files[0]));
  $("file").addEventListener("change", (e) => e.target.files[0] && onFile(e.target.files[0]));
  $("reset").addEventListener("click", reset);

  function setError(m) { $("error").textContent = m || ""; show($("error"), !!m); }

  function onFile(file) {
    setError(""); show($("notice"), false);
    const isVideo = file.type.startsWith("video/");
    if (src === "image" && isVideo) { setError("That is a video. Use the “Pick from video” tab."); return; }
    if (src === "video" && !isVideo) { setError("Choose a video file (MP4 or WebM) on this tab."); return; }
    if (!isVideo && !file.type.startsWith("image/")) { setError("Unsupported file type. Use a PNG/JPG image or an MP4 video."); return; }
    if (isVideo) {
      const v = $("video");
      v.onerror = () => { setError("This browser cannot play that video (AVI is not supported). Convert it to MP4 or export a still frame."); show($("vidpick"), false); show($("drop"), true); v.removeAttribute("src"); };
      v.src = URL.createObjectURL(file);
      show($("drop"), false); show($("vidpick"), true);
      return;
    }
    analyse(file);
  }

  $("grab").addEventListener("click", () => {
    const v = $("video");
    if (!v.videoWidth) return setError("The video is not ready yet.");
    const c = document.createElement("canvas"); c.width = v.videoWidth; c.height = v.videoHeight;
    c.getContext("2d").drawImage(v, 0, 0);
    c.toBlob((b) => analyse(new File([b], "frame.png", { type: "image/png" })), "image/png");
  });

  function reset() {
    current = null;
    show($("figure"), false); show($("layers"), false); show($("reset"), false); show($("notice"), false); setError("");
    ["tArea", "tConf", "tBox", "tPts"].forEach((i) => ($(i).textContent = "—"));
    const v = $("video"); v.pause(); v.removeAttribute("src"); v.load(); $("file").value = "";
    showSource();
  }

  async function post(path, body, isForm) {
    const r = await fetch(API + path, { method: "POST", headers: isForm ? undefined : { "Content-Type": "application/json" }, body: isForm ? body : JSON.stringify(body) });
    let j = null; try { j = await r.json(); } catch {}
    if (!r.ok) throw new Error((j && j.detail) || `Request failed (${r.status})`);
    return j;
  }

  async function analyse(file) {
    setError("");
    show($("busy"), true); $("busyText").textContent = "uploading";
    try {
      const fd = new FormData(); fd.append("file", file);
      const { file_url } = await post("/uploads", fd, true);
      $("busyText").textContent = "tracing";
      render(await post("/lv-outline/predict", { file_url }));
    } catch (e) {
      setError(e.message === "Failed to fetch" ? `Cannot reach the API at ${API}. Is the backend running?` : e.message);
    } finally { show($("busy"), false); }
  }

  /* ---------- drawing ---------- */
  // closed Catmull-Rom spline through the polygon vertices -> smooth SVG path (viewBox 0..1 scaled to W×H)
  function smooth(pts, W, H) {
    const n = pts.length, P = pts.map(([x, y]) => [x * W, y * H]);
    let d = `M${P[0][0].toFixed(1)} ${P[0][1].toFixed(1)}`;
    for (let i = 0; i < n; i++) {
      const p0 = P[(i - 1 + n) % n], p1 = P[i], p2 = P[(i + 1) % n], p3 = P[(i + 2) % n];
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += `C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
    }
    return d + "Z";
  }

  function render(r) {
    if (r.summary && r.summary.includes("weights not found")) {
      $("notice").innerHTML = "The model weights are not installed, so nothing was traced. Run <code>scripts/fetch_weights</code> (or place <code>lv_model.onnx</code> in <code>backend/app/lv_outline/weights/</code>) and restart the API.";
      show($("notice"), true); return;
    }
    current = r;
    const W = r.width, H = r.height;
    const img = $("img"); img.src = "data:image/png;base64," + r.original_image_base64;
    const svg = $("svg"); svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    show($("drop"), false); show($("vidpick"), false); show($("figure"), true); show($("layers"), true); show($("reset"), true);
    fit();

    const pts = r.contour || [];
    const trace = $("tracePath"), fill = $("fillPath"), box = $("bbox");
    if (pts.length < 3) {
      trace.setAttribute("d", ""); fill.setAttribute("d", ""); box.setAttribute("width", 0);
      ["tArea", "tConf", "tBox", "tPts"].forEach((i) => ($(i).textContent = "—"));
      $("notice").textContent = r.summary; show($("notice"), true); return;
    }
    const d = smooth(pts, W, H);
    fill.setAttribute("d", d); trace.setAttribute("d", d);
    const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    const x0 = Math.min(...xs) * W, x1 = Math.max(...xs) * W, y0 = Math.min(...ys) * H, y1 = Math.max(...ys) * H;
    box.setAttribute("x", x0); box.setAttribute("y", y0); box.setAttribute("width", x1 - x0); box.setAttribute("height", y1 - y0);

    // animated pen stroke
    const len = trace.getTotalLength();
    trace.style.transition = "none"; trace.style.strokeDasharray = len; trace.style.strokeDashoffset = len;
    fill.style.opacity = 0;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      trace.style.transition = "stroke-dashoffset 1.6s cubic-bezier(.4,.1,.2,1)"; trace.style.strokeDashoffset = 0;
      setTimeout(() => (fill.style.opacity = $("lFill").checked ? 1 : 0), 1300);
    }));

    $("tArea").textContent = (r.area_fraction * 100).toFixed(1) + "%";
    $("tConf").textContent = (r.confidence * 100).toFixed(0) + "%";
    $("tBox").textContent = `${Math.round((x1 - x0) / W * 100)}% × ${Math.round((y1 - y0) / H * 100)}%`;
    $("tPts").textContent = pts.length;
    applyLayers();
  }

  function fit() {
    if (!current) return;
    const f = $("figure"), k = Math.min(f.clientWidth / current.width, f.clientHeight / current.height);
    $("frame").style.width = current.width * k + "px"; $("frame").style.height = current.height * k + "px";
  }
  window.addEventListener("resize", fit);

  function applyLayers() {
    $("fillPath").style.display = $("lFill").checked ? "" : "none";
    $("fillPath").style.opacity = 1;
    $("tracePath").style.display = $("lTrace").checked ? "" : "none";
    $("bbox").style.display = $("lBox").checked ? "" : "none";
  }
  ["lFill", "lTrace", "lBox"].forEach((i) => $(i).addEventListener("change", applyLayers));
})();
