<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aizawl Landslide Risk Map — SIH26001</title>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
<link rel="stylesheet" href="https://unpkg.com/leaflet-gesture-handling/dist/leaflet-gesture-handling.min.css" type="text/css">

<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: 'Segoe UI', Arial, sans-serif; }

  /* ===== TOPBAR ===== */
  #topbar {
    background: linear-gradient(90deg, #0f172a, #1e3a8a);
    color: white; padding: 10px 18px;
    display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: 8px;
  }
  #topbar h1 { font-size: 16px; margin: 0; }
  #topbar .subtitle { font-size: 11px; opacity: 0.8; margin-top: 2px; }
  #topbar-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  #status-pill { background: #22c55e; color: white; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; }
  #status-pill.offline { background: #ef4444; }
  .icon-btn { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.25); color: white; padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; }
  .icon-btn:hover { background: rgba(255,255,255,0.22); }
  #mobile-toggle { display:none; }
  #mini-stats { display: flex; gap: 18px; }
  .stat-box { text-align: center; }
  .stat-num { display:block; font-size:18px; font-weight:700; color:white; }
  .stat-label { font-size:9.5px; color:rgba(255,255,255,0.7); text-transform:uppercase; letter-spacing:0.3px; }

  .live-dot {
    display:inline-block; width:7px; height:7px; border-radius:50%;
    background: white; margin-right:6px; vertical-align:middle;
    animation: blinkDot 1.4s ease-in-out infinite;
  }
  @keyframes blinkDot { 0%,100% { opacity:1; } 50% { opacity:0.3; } }

  /* Sidebar cards staggered fade-in */
  @keyframes cardIn { from { opacity:0; transform: translateX(-6px);} to { opacity:1; transform: translateX(0);} }
  .area-card { animation: cardIn 0.3s ease-out backwards; }

  /* Basemap crossfade */
  .leaflet-tile-pane { transition: opacity 0.35s ease; }
  .tile-fading { opacity: 0.3; }

  #topbar { flex-wrap: wrap; }
  @media (max-width: 900px) { #mini-stats { display:none; } }

  /* ===== LAYOUT ===== */
  #layout { display: flex; height: calc(100vh - 58px); position: relative; }
  #sidebar { width: 300px; background: #f8fafc; overflow-y: auto; border-right: 1px solid #e2e8f0; display:flex; flex-direction:column; flex-shrink:0; }
  #map { flex: 1; position: relative; min-width: 0; }

  #search-box { padding: 10px 12px; border-bottom: 1px solid #e2e8f0; }
  #search-input { width:100%; padding:7px 10px; border:1px solid #cbd5e1; border-radius:6px; font-size:12.5px; }

  #layer-toggles { padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-size: 12px; }
  #layer-toggles label { display:flex; align-items:center; gap:6px; margin-bottom:6px; color:#334155; cursor:pointer; transition: color 0.15s ease; }
  #layer-toggles label:hover { color: #1e3a8a; }
  #layer-toggles input[type="checkbox"] { accent-color: #1e3a8a; transform: scale(1.05); transition: transform 0.1s ease; cursor:pointer; }
  #layer-toggles input[type="checkbox"]:active { transform: scale(0.9); }

  #filter-header {
    padding: 8px 12px; font-size:11.5px; font-weight:600; color:#475569; cursor:pointer;
    display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #e2e8f0;
    user-select:none;
  }
  #filter-arrow { transition: transform 0.2s ease; }
  #filter-arrow.collapsed { transform: rotate(-90deg); }
  #filter-bar { padding: 10px 12px; border-bottom: 1px solid #e2e8f0; display:flex; gap:6px; flex-wrap:wrap;
    max-height: 200px; overflow:hidden; transition: max-height 0.25s ease, padding 0.25s ease; }
  #filter-bar.collapsed { max-height: 0; padding-top:0; padding-bottom:0; border-bottom:none; }
  .filter-chip { font-size: 11px; padding: 4px 10px; border-radius: 14px; border: 1px solid #cbd5e1; background: white; cursor: pointer; color:#334155; }
  .filter-chip.active { color: white; border-color: transparent; }
  .filter-chip[data-level="All"].active { background:#334155; }
  .filter-chip[data-level="Low"].active { background:#22c55e; }
  .filter-chip[data-level="Moderate"].active { background:#eab308; }
  .filter-chip[data-level="High"].active { background:#f97316; }
  .filter-chip[data-level="Critical"].active { background:#ef4444; }

  #area-list-label { padding:10px 16px 4px 16px; font-size:12px; color:#64748b; font-weight:600; }
  .area-card { padding: 12px 16px; border-bottom: 1px solid #e2e8f0; cursor: pointer; }
  .area-card:hover { background: #eef2ff; }
  .area-card .name { font-weight: 600; font-size: 13.5px; color: #0f172a; }
  .area-card .score-row { display: flex; align-items: center; margin-top: 4px; }
  .area-card .dot { width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; flex-shrink:0; }
  .area-card .score-text { font-size: 12px; color: #64748b; }
  .area-card .freshness { font-size: 10.5px; color: #94a3b8; margin-top: 3px; }
  .no-results { padding:16px; color:#94a3b8; font-size:12.5px; }

  /* ===== ANIMATIONS ===== */
  /* Critical risk markers pulse — draws the eye to the most dangerous
     zones first, exactly like a real monitoring dashboard would */
  @keyframes pulseGlow {
    0%, 100% { filter: drop-shadow(0 0 0px #ef4444); opacity: 1; }
    50% { filter: drop-shadow(0 0 9px #ef4444); opacity: 0.7; }
  }
  .critical-marker-pulse { animation: pulseGlow 1.6s ease-in-out infinite; }

  @keyframes pulseGlowHigh {
    0%, 100% { filter: drop-shadow(0 0 0px #f97316); }
    50% { filter: drop-shadow(0 0 6px #f97316); }
  }
  .high-marker-pulse { animation: pulseGlowHigh 2.2s ease-in-out infinite; }

  /* Explainability panel slides in smoothly instead of popping open */
  @keyframes panelIn { from { opacity:0; transform: translateY(-10px) scale(0.98); } to { opacity:1; transform: translateY(0) scale(1); } }
  #explain-panel.open { animation: panelIn 0.22s ease-out; }

  /* Historical (triangle) markers fade in when the layer is toggled on */
  @keyframes markerFadeIn { from { opacity:0; transform: translateY(-4px); } to { opacity:1; transform: translateY(0); } }
  .historical-marker-fade { animation: markerFadeIn 0.35s ease-out; }

  /* Sidebar cards + status pill + filter chips feel responsive, not static */
  .area-card { transition: background 0.15s ease; }
  #status-pill { transition: background 0.3s ease; }
  .filter-chip { transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease; }
  .icon-btn { transition: background 0.15s ease, transform 0.15s ease; }
  .icon-btn:active { transform: scale(0.96); }
  #status-panel .tag { transition: background 0.3s ease; }

  .legend { position: absolute; bottom: 20px; right: 20px; background: white; padding: 10px 14px; border-radius: 8px; box-shadow: 0 1px 8px rgba(0,0,0,0.25); z-index: 1000; font-size: 12.5px; }
  .legend div { margin-bottom: 4px; }
  .legend .dot { display: inline-block; width: 11px; height: 11px; border-radius: 50%; margin-right: 6px; }
  .legend .tri { display:inline-block; width:0; height:0; border-left:5px solid transparent; border-right:5px solid transparent; border-bottom:9px solid #6d28d9; margin-right:6px; }

  /* ===== DATA PROVENANCE / STATUS PANEL ===== */
  #status-panel {
    position: absolute; bottom: 20px; left: 20px; background: white;
    padding: 10px 14px; border-radius: 8px; box-shadow: 0 1px 8px rgba(0,0,0,0.25);
    z-index: 1000; font-size: 11.5px; max-width: 230px;
  }
  #status-panel b { display:block; margin-bottom: 6px; font-size:12px; }
  #status-panel .row { display:flex; justify-content:space-between; margin-bottom:3px; }
  #status-panel .tag { padding:1px 7px; border-radius:8px; font-size:10px; font-weight:600; color:white; }
  .tag-live { background:#22c55e; } .tag-demo { background:#f59e0b; } .tag-proto { background:#6366f1; } .tag-research { background:#0ea5e9; }

  /* ===== EXPLAIN PANEL ===== */
  #explain-panel { position: absolute; top: 16px; right: 16px; width: 310px; background: white; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 1001; padding: 16px; display: none; max-height: 88%; overflow-y: auto; }
  #explain-panel.open { display: block; }
  #explain-panel h3 { margin: 0 0 2px 0; font-size: 15px; color:#0f172a; }
  #explain-panel .risk-badge { display:inline-block; padding:3px 10px; border-radius:12px; color:white; font-size:11px; font-weight:600; margin-top:6px; }
  #explain-panel .close-btn { position:absolute; top:12px; right:14px; cursor:pointer; color:#94a3b8; font-size:16px; background:none; border:none; }

  .split-row { display:flex; gap:8px; margin-top:12px; }
  .split-box { flex:1; background:#f8fafc; border-radius:8px; padding:8px 10px; text-align:center; }
  .split-box .split-label { font-size:10px; color:#64748b; text-transform:uppercase; }
  .split-box .split-value { font-size:15px; font-weight:700; margin-top:2px; }

  #explain-why { margin-top:12px; background:#fffbeb; border:1px solid #fde68a; border-radius:8px; padding:10px 12px; font-size:12px; }
  #explain-why b { display:block; margin-bottom:6px; font-size:11.5px; color:#92400e; }
  #explain-why ol { margin:0; padding-left:18px; }
  #explain-why li { margin-bottom:3px; color:#78350f; }

  #explain-panel .factor-row { margin-top: 10px; }
  #explain-panel .factor-label { display:flex; justify-content:space-between; font-size:11.5px; color:#475569; margin-bottom:3px; }
  #explain-panel .factor-bar-bg { background:#e2e8f0; border-radius:6px; height:7px; overflow:hidden; }
  #explain-panel .factor-bar-fill { height:100%; border-radius:6px; }
  #explain-panel .source-note { margin-top:14px; font-size:10.5px; color:#94a3b8; border-top:1px solid #e2e8f0; padding-top:10px; }
  #explain-panel .confidence-note { margin-top:8px; font-size:10.5px; color:#b45309; background:#fffbeb; padding:6px 8px; border-radius:6px; }

  #alert-log-panel {
    position: absolute; top: 16px; right: 16px; width: 310px; background: white;
    border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 1002;
    padding: 14px; display: none; max-height: 80%; overflow-y: auto;
  }
  #alert-log-panel.open { display: block; animation: panelIn 0.22s ease-out; }
  #alert-log-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
  #alert-log-notice { font-size:10.5px; color:#b45309; background:#fffbeb; padding:8px 10px; border-radius:6px; margin-bottom:10px; }
  .alert-entry { border-left: 3px solid #ef4444; background:#fef2f2; border-radius:6px; padding:8px 10px; margin-bottom:8px; font-size:11.5px; }
  .alert-entry.high { border-left-color:#f97316; background:#fff7ed; }
  .alert-entry .alert-time { color:#94a3b8; font-size:10px; }
  .alert-entry .alert-title { font-weight:600; color:#0f172a; margin:2px 0; }
  .alert-entry .alert-recipients { color:#64748b; font-size:10.5px; }
  #alert-badge { background:#ef4444; color:white; border-radius:10px; padding:1px 6px; font-size:10px; margin-left:4px; }
  #alert-badge:empty { display:none; }

  #basemap-toggle { position:absolute; top:16px; left:72px; z-index:1000; background:white; border-radius:8px; box-shadow:0 1px 8px rgba(0,0,0,0.25); overflow:hidden; display:flex; }
  #basemap-toggle button { border:none; background:white; padding:8px 14px; font-size:12px; cursor:pointer; color:#334155; transition: background 0.15s ease, color 0.15s ease; }
  #basemap-toggle button.active { background:#1e3a8a; color:white; }

  /* Leaflet ka zoom control thoda neat spacing ke saath */
  .leaflet-control-zoom { margin-top: 16px !important; margin-left: 16px !important; }
  /* Scale bar ko status-panel (jo bhi bottom-left mein hai) se upar rakho, overlap na ho */
  .leaflet-bottom.leaflet-left .leaflet-control-scale { margin-bottom: 145px !important; margin-left: 16px !important; }

  /* ===== MOBILE ===== */
  /* ===== SYNC BANNER (offline queue status, visible across whole page) ===== */
  #sync-banner {
    background:#f59e0b; color:white; text-align:center; padding:8px; font-size:12.5px;
    display:none; align-items:center; justify-content:center; gap:8px;
  }
  #sync-banner.show { display:flex; }
  #sync-banner.synced { background:#22c55e; }

  /* ===== REPORT HAZARD MODAL ===== */
  #report-modal-overlay {
    position:fixed; inset:0; background:rgba(15,23,42,0.6); z-index:3000;
    display:none; align-items:flex-start; justify-content:center; overflow-y:auto; padding:20px 12px;
  }
  #report-modal-overlay.show { display:flex; animation: fieldIn 0.2s ease-out; }
  #report-modal-card {
    background:#f1f5f9; border-radius:14px; max-width:520px; width:100%; margin-top:20px;
    animation: successPop 0.3s cubic-bezier(0.34,1.56,0.64,1); overflow:hidden;
  }
  #report-modal-header {
    background: linear-gradient(90deg,#0f172a,#1e3a8a); color:white; padding:16px 18px;
    display:flex; justify-content:space-between; align-items:flex-start;
  }
  #report-modal-header h2 { margin:0; font-size:16px; }
  .report-subtitle { font-size:11px; opacity:0.85; margin-top:3px; }
  #report-modal-close {
    background:rgba(255,255,255,0.15); border:none; color:white; width:28px; height:28px;
    border-radius:50%; cursor:pointer; font-size:14px;
  }
  #report-modal-body { padding:16px; max-height:75vh; overflow-y:auto; }

  @keyframes fieldIn { from{opacity:0; transform:translateY(8px);} to{opacity:1; transform:translateY(0);} }
  @keyframes successPop { from{transform:scale(0.7); opacity:0;} to{transform:scale(1); opacity:1;} }

  .field-group { background:white; border-radius:12px; padding:14px; margin-bottom:12px;
    box-shadow:0 1px 4px rgba(0,0,0,0.06); animation: fieldIn 0.35s ease-out backwards; }
  .field-label { font-size:12.5px; font-weight:600; color:#334155; margin-bottom:8px; display:flex; align-items:center; gap:6px; }
  .required-star { color:#ef4444; }

  #report-modal-body input[type=text], #report-modal-body textarea {
    width:100%; padding:10px 12px; border:1.5px solid #e2e8f0; border-radius:8px;
    font-size:14px; font-family:inherit; transition: border-color 0.15s ease;
  }
  #report-modal-body input[type=text]:focus, #report-modal-body textarea:focus { outline:none; border-color:#1e3a8a; }
  #report-modal-body textarea { resize:vertical; min-height:60px; }

  .toggle-row { display:flex; gap:8px; }
  .toggle-btn { flex:1; padding:10px; text-align:center; border:1.5px solid #e2e8f0; border-radius:8px;
    cursor:pointer; font-size:13px; color:#64748b; transition: all 0.15s ease; }
  .toggle-btn.active { border-color:#1e3a8a; background:#eef2ff; color:#1e3a8a; font-weight:600; transform:scale(1.02); }

  .obs-grid { display:grid; grid-template-columns: repeat(3,1fr); gap:8px; }
  .obs-card { border:1.5px solid #e2e8f0; border-radius:10px; padding:10px 6px; text-align:center;
    cursor:pointer; font-size:11px; color:#64748b; transition: all 0.15s ease; }
  .obs-card .obs-icon { font-size:20px; display:block; margin-bottom:4px; }
  .obs-card.active { border-color:#1e3a8a; background:#eef2ff; color:#1e3a8a; font-weight:600; transform:scale(1.04); }

  .severity-row { display:flex; gap:8px; }
  .sev-btn { flex:1; padding:10px; text-align:center; border-radius:8px; cursor:pointer;
    font-size:12.5px; font-weight:600; color:white; opacity:0.4; transition: all 0.15s ease; border:none; }
  .sev-btn.active { opacity:1; transform:scale(1.05); box-shadow:0 2px 8px rgba(0,0,0,0.2); }
  .sev-low { background:#22c55e; } .sev-medium { background:#f59e0b; } .sev-high { background:#ef4444; }

  #location-map { height:170px; border-radius:10px; margin-top:8px; }
  #locate-btn { margin-top:8px; width:100%; padding:9px; border:1.5px dashed #1e3a8a; background:#eef2ff;
    color:#1e3a8a; border-radius:8px; font-size:12.5px; cursor:pointer; transition: background 0.15s ease; }
  #coords-display { font-size:11px; color:#64748b; margin-top:6px; text-align:center; }

  #photo-drop { border:2px dashed #cbd5e1; border-radius:10px; padding:18px; text-align:center;
    cursor:pointer; color:#94a3b8; font-size:12.5px; transition: border-color 0.15s ease; }
  #photo-drop:hover { border-color:#1e3a8a; }
  #photo-preview { margin-top:10px; display:none; text-align:center; animation: fieldIn 0.3s ease-out; }
  #photo-preview img { max-width:100%; max-height:160px; border-radius:8px; }
  #photo-preview .remove-photo { display:block; margin-top:6px; color:#ef4444; font-size:11.5px; cursor:pointer; }

  #report-submit-btn { width:100%; padding:14px; background:#1e3a8a; color:white; border:none; border-radius:10px;
    font-size:14.5px; font-weight:600; cursor:pointer; transition: background 0.15s ease, transform 0.1s ease;
    display:flex; align-items:center; justify-content:center; gap:8px; }
  #report-submit-btn:active { transform:scale(0.98); }
  #report-submit-btn:disabled { background:#94a3b8; cursor:not-allowed; }
  .spinner { width:16px; height:16px; border:2px solid rgba(255,255,255,0.4); border-top-color:white;
    border-radius:50%; animation: spin 0.7s linear infinite; display:none; }
  @keyframes spin { to { transform:rotate(360deg); } }

  #success-overlay { position:fixed; inset:0; background:rgba(15,23,42,0.55); display:none;
    align-items:center; justify-content:center; z-index:3500; padding:20px; }
  #success-overlay.show { display:flex; animation: fieldIn 0.2s ease-out; }
  #success-card { background:white; border-radius:16px; padding:28px 24px; text-align:center; max-width:340px;
    animation: successPop 0.4s cubic-bezier(0.34,1.56,0.64,1); }
  .success-icon { width:56px; height:56px; border-radius:50%; background:#22c55e; color:white; font-size:28px;
    display:flex; align-items:center; justify-content:center; margin:0 auto 14px auto; animation: checkPulse 0.6s ease-out; }
  .success-icon.offline { background:#f59e0b; }
  @keyframes checkPulse { 0%{transform:scale(0);} 60%{transform:scale(1.15);} 100%{transform:scale(1);} }
  #success-status-badge { display:inline-block; margin-top:10px; padding:4px 12px; border-radius:12px;
    background:#fef3c7; color:#92400e; font-size:11px; font-weight:600; animation: badgePulse 1.6s ease-in-out infinite; }
  @keyframes badgePulse { 0%,100%{opacity:1;} 50%{opacity:0.6;} }
  #success-card button { margin-top:16px; padding:10px 20px; border:none; background:#f1f5f9; border-radius:8px;
    color:#334155; font-size:13px; cursor:pointer; }
  #auth-modal-overlay {
    position:fixed; inset:0; background:rgba(15,23,42,0.6); z-index:3200;
    display:none; align-items:center; justify-content:center; padding:20px;
  }
  #auth-modal-overlay.show { display:flex; animation: fieldIn 0.2s ease-out; }
  #auth-modal-card {
    background:#f1f5f9; border-radius:14px; max-width:360px; width:100%; padding:20px;
    position:relative; animation: successPop 0.3s cubic-bezier(0.34,1.56,0.64,1);
  }
  #auth-modal-title { margin:0 0 14px 0; font-size:15px; color:#0f172a; text-align:center; }
  .report-modal-close {
    position:absolute; top:14px; right:14px; background:#e2e8f0; border:none; width:26px; height:26px;
    border-radius:50%; cursor:pointer; font-size:12px;
  }
  .auth-tabs { display:flex; gap:8px; margin-bottom:14px; }
  .auth-tab { flex:1; text-align:center; padding:8px; border-radius:8px; cursor:pointer; font-size:12.5px;
    color:#64748b; background:white; transition: all 0.15s ease; }
  .auth-tab.active { background:#1e3a8a; color:white; font-weight:600; }
  #auth-submit-btn { width:100%; padding:12px; background:#1e3a8a; color:white; border:none; border-radius:10px;
    font-size:14px; font-weight:600; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px; }
  #auth-submit-btn:disabled { background:#94a3b8; }
  .error-text { color:#ef4444; font-size:11.5px; margin-top:6px; display:none; }

  @media (max-width: 720px) {
    #topbar h1 { font-size:14px; }
    #layout { flex-direction: column; height: auto; }
    #sidebar {
      width: 100%; order: 2; max-height: 0; overflow: hidden;
      transition: max-height 0.25s ease; border-right:none; border-top:1px solid #e2e8f0;
    }
    #sidebar.expanded { max-height: 60vh; overflow-y:auto; }
    #map { height: 60vh; order: 1; }
    #mobile-toggle { display:block; }
    #explain-panel { width: calc(100% - 32px); left:16px; right:16px; }
    .legend { font-size: 11px; padding: 7px 10px; }
    #status-panel { max-width: 160px; font-size: 10.5px; }
  }
</style>
</head>
<body>

<div id="topbar">
  <div>
    <h1>🏔️ Aizawl Landslide Risk Map</h1>
    <div class="subtitle">SIH26001 — MDoNER Early Warning System</div>
  </div>
  <div id="mini-stats">
    <div class="stat-box"><span class="stat-num" id="stat-total">0</span><span class="stat-label">Areas Monitored</span></div>
    <div class="stat-box"><span class="stat-num" id="stat-critical" style="color:#fca5a5;">0</span><span class="stat-label">Critical Now</span></div>
    <div class="stat-box"><span class="stat-num" id="stat-history">0</span><span class="stat-label">Historical Events</span></div>
  </div>
  <div id="topbar-right">
    <button class="icon-btn" id="auth-btn" onclick="openAuthModal()">🔑 Login</button>
    <button class="icon-btn" id="lang-toggle-btn" onclick="toggleLanguage()">🌐 EN</button>
    <button class="icon-btn" id="alert-log-btn" onclick="toggleAlertLog()">🔔 Alerts <span id="alert-badge"></span></button>
    <button class="icon-btn" id="report-hazard-btn" onclick="openReportModal()" style="background:#dc2626;border-color:#dc2626;">📍 Report Hazard</button>
    <button class="icon-btn" id="play-timeline-btn" onclick="playTimeline()">▶ Play History (1992–2024)</button>
    <button class="icon-btn" id="mobile-toggle" onclick="toggleSidebar()">☰ Areas</button>
    <button class="icon-btn" onclick="toggleFullscreen()">⛶ Fullscreen</button>
    <div id="status-pill"><span class="live-dot"></span>Connecting...</div>
  </div>
</div>

<div id="sync-banner">
  <span id="sync-banner-text">⏳ 0 reports waiting to sync</span>
</div>

<div id="layout">
  <div id="sidebar">
    <div id="search-box">
      <input id="search-input" type="text" placeholder="Search area name..." oninput="renderAreas(currentAreas)">
    </div>
    <div id="layer-toggles">
      <label><input type="checkbox" id="toggle-live" checked onchange="renderAreas(currentAreas)"> Current Risk Areas (live)</label>
      <label><input type="checkbox" id="toggle-historical" checked onchange="renderHistorical()"> Historical Events (research)</label>
    </div>
    <div id="filter-header" onclick="toggleFilterBar()">
      <span>Risk Level Filter</span>
      <span id="filter-arrow">▾</span>
    </div>
    <div id="filter-bar">
      <div class="filter-chip active" data-level="All" onclick="setFilter('All')">All</div>
      <div class="filter-chip" data-level="Low" onclick="setFilter('Low')">Low</div>
      <div class="filter-chip" data-level="Moderate" onclick="setFilter('Moderate')">Moderate</div>
      <div class="filter-chip" data-level="High" onclick="setFilter('High')">High</div>
      <div class="filter-chip" data-level="Critical" onclick="setFilter('Critical')">Critical</div>
    </div>
    <div id="area-list-label">AREAS (click for details)</div>
    <div id="area-list" style="flex:1;">Loading...</div>
  </div>

  <div id="map">
    <div id="basemap-toggle">
      <button id="btn-street" class="active" onclick="setBasemap('street')">Street</button>
      <button id="btn-satellite" onclick="setBasemap('satellite')">Satellite</button>
    </div>

    <div class="legend">
      <b>Risk Level</b>
      <div><span class="dot" style="background:#22c55e;"></span> Low</div>
      <div><span class="dot" style="background:#eab308;"></span> Moderate</div>
      <div><span class="dot" style="background:#f97316;"></span> High</div>
      <div><span class="dot" style="background:#ef4444;"></span> Critical</div>
      <div><span class="tri"></span> Historical event</div>
    </div>

    <div id="status-panel">
      <b>System / Data Status</b>
      <div class="row"><span>Backend</span><span id="tag-backend" class="tag tag-demo">—</span></div>
      <div class="row"><span>Risk Model</span><span class="tag tag-proto">PROTOTYPE</span></div>
      <div class="row"><span>Rainfall</span><span class="tag tag-demo">DEMO / EST.</span></div>
      <div class="row"><span>History</span><span class="tag tag-research">RESEARCH</span></div>
    </div>

    <div id="explain-panel">
      <button class="close-btn" onclick="closeExplain()">✕</button>
      <h3 id="explain-name">—</h3>
      <span id="explain-badge" class="risk-badge">—</span>

      <div class="split-row">
        <div class="split-box">
          <div class="split-label">Baseline Susceptibility</div>
          <div class="split-value" id="explain-baseline">—</div>
        </div>
        <div class="split-box">
          <div class="split-label">Current Trigger</div>
          <div class="split-value" id="explain-trigger">—</div>
        </div>
      </div>

      <div id="explain-why">
        <b>WHY THIS AREA IS HIGH RISK</b>
        <ol id="explain-why-list"></ol>
      </div>

      <div id="explain-factors"></div>
      <div id="explain-source" class="source-note"></div>
      <div class="confidence-note">⚠️ Locality-level approximate coordinates &amp; prototype-estimated factor inputs — not GPS-surveyed or field-measured. See methodology note in presentation.</div>
    </div>

    <div id="alert-log-panel">
      <div id="alert-log-header">
        <b>🔔 Alert Log</b>
        <button class="close-btn" onclick="toggleAlertLog()">✕</button>
      </div>
      <div id="alert-log-notice">⚠️ SIMULATED alerts — no real SMS is sent. Shows how the system would notify authorities when a real SMS/telecom gateway is integrated.</div>
      <div id="alert-log-list"><div class="no-results">No alerts yet — alerts appear when an area's risk becomes High or Critical.</div></div>
    </div>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
  integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script src="https://unpkg.com/leaflet-gesture-handling"></script>

<script>
  // =====================================================================
  // CONFIG
  // =====================================================================
  const BACKEND_URL = "https://sih-landslide-backend.onrender.com";
  // Local testing ke liye:
  // const BACKEND_URL = "http://127.0.0.1:5000";

  // =====================================================================
  // DATA — Live risk fallback (agar backend na chale)
  // =====================================================================
  const FALLBACK_DATA = [
    { area_name: "South Hlimen area", latitude: 23.6716, longitude: 92.7181,
      risk_score: 60, risk_level: "High",
      slope_degree: 40, rainfall_24h_mm: 30, rainfall_antecedent_mm: 40, road_distance_m: 300,
      geology_score: 8, landuse_score: 7, drainage_score: 4,
      data_source: "Prototype estimate — Mizoram SDMP 2020 context", last_updated: null },
    { area_name: "Laipuitlang / Ramhlun Venglai", latitude: 23.735, longitude: 92.725,
      risk_score: 77, risk_level: "High",
      slope_degree: 45, rainfall_24h_mm: 40, rainfall_antecedent_mm: 30, road_distance_m: 150,
      geology_score: 7, landuse_score: 6, drainage_score: 5,
      data_source: "Prototype estimate — Science Vision 2015 context", last_updated: null },
    { area_name: "Aizawl City (rainfall-trigger scenario)", latitude: 23.7271, longitude: 92.7176,
      risk_score: 89, risk_level: "Critical",
      slope_degree: 45, rainfall_24h_mm: 205, rainfall_antecedent_mm: 110, road_distance_m: 150,
      geology_score: 7, landuse_score: 6, drainage_score: 5,
      data_source: "Prototype estimate — Sangi et al. 2025 rainfall reference", last_updated: null }
  ];

  // =====================================================================
  // DATA — Historical events (separate layer, from Saif's research pack)
  // These are FIXED research facts, not live risk — never mixed with
  // the live risk_scores layer.
  // =====================================================================
  const HISTORICAL_EVENTS = [
    { name: "South Hlimen — quarry rockslide", latitude: 23.6716, longitude: 92.7181,
      date: "9 Aug 1992", confidence: "Verified (govt. record)",
      description: "66 deaths, 17 houses damaged. Recurrence noted 2005.",
      source: "Mizoram State Disaster Management Plan 2020" },
    { name: "Hunthar — recurrent sinking (NH-54)", latitude: 23.745, longitude: 92.735,
      date: "1992–2011 (11 recorded years)", confidence: "Verified (govt. record)",
      description: "Recurrent sinking affecting NH-54 and houses.",
      source: "Mizoram State Disaster Management Plan 2020" },
    { name: "Armed Veng — slump", latitude: 23.728, longitude: 92.710,
      date: "2004–2005", confidence: "Verified (govt. record)",
      description: "100+ houses affected, 25 vacated.",
      source: "Mizoram State Disaster Management Plan 2020" },
    { name: "Chandmari West — slump", latitude: 23.740, longitude: 92.715,
      date: "2005", confidence: "Verified (govt. record)",
      description: "30 houses vacated.",
      source: "Mizoram State Disaster Management Plan 2020" },
    { name: "Laipuitlang → Ramhlun Venglai — rockslide", latitude: 23.735, longitude: 92.725,
      date: "11 May 2013, ~3:24am", confidence: "Verified (peer-reviewed case study)",
      description: "17 deaths, 15 houses destroyed. Steep slope + heavy rainfall + rock bedding + human modification cited as causes.",
      source: "Chenkual (2015), Science Vision 15(1)" },
    { name: "Aizawl multi-site — Cyclone Remal cluster", latitude: 23.7271, longitude: 92.7176,
      date: "28 May 2024", confidence: "Verified (peer-reviewed study)",
      description: "34 fatalities, 54 houses evacuated, 14 sites studied. 205mm rainfall in preceding 24h.",
      source: "Sangi et al. (2025), Landslides 22(5)" }
  ];

  // =====================================================================
  // MAP SETUP
  // =====================================================================
  // Gesture-handling sirf DESKTOP (mouse/trackpad) ke liye — mobile touch
  // devices pe ye ek "use two fingers" overlay dikhata hai jo map ko
  // dhak deta hai aur "crash jaisa" lagta hai. Touch devices ko iski
  // zaroorat hi nahi — unka pinch-zoom/drag already Leaflet mein
  // built-in kaam karta hai.
  var isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);

  var map = L.map('map', {
    gestureHandling: !isTouchDevice,
    zoomControl: false,
    maxZoom: 22
  }).setView([23.7271, 92.7176], 12);
  L.control.zoom({ position: 'topleft' }).addTo(map);
  L.control.scale({ position: 'bottomleft', imperial: false }).addTo(map);

  var streetLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 22, maxNativeZoom: 19, attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  var satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 22, maxNativeZoom: 19, attribution: 'Tiles © Esri — Esri, Maxar, Earthstar Geographics'
  });

  function setBasemap(type) {
    var pane = document.querySelector('.leaflet-tile-pane');
    if (pane) pane.classList.add('tile-fading');
    setTimeout(function() { if (pane) pane.classList.remove('tile-fading'); }, 350);

    if (type === 'satellite') {
      map.removeLayer(streetLayer); satelliteLayer.addTo(map);
      document.getElementById('btn-satellite').classList.add('active');
      document.getElementById('btn-street').classList.remove('active');
    } else {
      map.removeLayer(satelliteLayer); streetLayer.addTo(map);
      document.getElementById('btn-street').classList.add('active');
      document.getElementById('btn-satellite').classList.remove('active');
    }
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen().catch(function() {
          console.warn("Fullscreen is not supported on this device/browser.");
        });
      }
    } else {
      if (document.exitFullscreen) document.exitFullscreen();
    }
  }

  function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('expanded');
  }

  function getRiskColor(level) {
    if (level === "Critical") return "#ef4444";
    if (level === "High") return "#f97316";
    if (level === "Moderate") return "#eab308";
    return "#22c55e";
  }

  function timeAgo(isoString) {
    if (!isoString) return "Prototype/reference data (not a live timestamp)";
    var diffMs = Date.now() - new Date(isoString).getTime();
    var mins = Math.round(diffMs / 60000);
    if (mins < 1) return "Updated just now";
    if (mins < 60) return "Updated " + mins + " min ago";
    var hrs = Math.round(mins / 60);
    if (hrs < 24) return "Updated " + hrs + " hr ago";
    return "Updated " + Math.round(hrs / 24) + " days ago";
  }

  // =====================================================================
  // LIVE RISK MARKERS
  // =====================================================================
  var markerRefs = {};
  var historicalRefs = [];
  var currentAreas = [];
  var activeFilter = "All";

  function toggleFilterBar() {
    document.getElementById('filter-bar').classList.toggle('collapsed');
    document.getElementById('filter-arrow').classList.toggle('collapsed');
  }

  function setFilter(level) {
    activeFilter = level;
    document.querySelectorAll('.filter-chip').forEach(function(c) {
      c.classList.toggle('active', c.dataset.level === level);
    });
    renderAreas(currentAreas);
  }

  function renderAreas(areas) {
    currentAreas = areas;
    Object.values(markerRefs).forEach(function(m) { map.removeLayer(m); });
    markerRefs = {};

    var showLive = document.getElementById('toggle-live').checked;
    var searchText = (document.getElementById('search-input').value || "").toLowerCase();

    var visible = areas.filter(function(a) {
      var matchesFilter = activeFilter === "All" || a.risk_level === activeFilter;
      var matchesSearch = a.area_name.toLowerCase().indexOf(searchText) !== -1;
      return matchesFilter && matchesSearch;
    });

    var listHtml = "";
    visible.forEach(function(area, idx) {
      var color = getRiskColor(area.risk_level);

      if (showLive) {
        var pulseClass = "";
        if (area.risk_level === "Critical") pulseClass = "critical-marker-pulse";
        else if (area.risk_level === "High") pulseClass = "high-marker-pulse";

        var marker = L.circleMarker([area.latitude, area.longitude], {
          radius: 13, fillColor: color, color: "#ffffff", weight: 2, fillOpacity: 0.9,
          className: pulseClass
        }).addTo(map);
        // Hover tooltip — quick preview cheezein click se pehle hi dikh jayein
        marker.bindTooltip(area.area_name + " — " + area.risk_level + " (" + area.risk_score + "/100)", { direction: "top", offset: [0,-10] });
        marker.on('click', function() { openExplain(area); });
        markerRefs[area.area_name] = marker;
      }

      listHtml += "<div class='area-card' style='animation-delay:" + (idx*0.05) + "s' onclick='flyToArea(\"" + area.area_name.replace(/"/g,'&quot;') + "\")'>" +
        "<div class='name'>" + area.area_name + "</div>" +
        "<div class='score-row'><span class='dot' style='background:" + color + "'></span>" +
        "<span class='score-text'>" + area.risk_level + " — " + area.risk_score + "/100</span></div>" +
        "<div class='freshness'>" + timeAgo(area.last_updated) + "</div>" +
        "</div>";
    });
    document.getElementById("area-list").innerHTML = listHtml || "<div class='no-results'>Koi area match nahi hua</div>";
  }

  window.flyToArea = function(name) {
    var area = currentAreas.find(function(a) { return a.area_name === name; });
    var marker = markerRefs[name];
    if (marker) { map.flyTo(marker.getLatLng(), 14); }
    if (area) openExplain(area);
  };

  // =====================================================================
  // HISTORICAL EVENTS LAYER (separate, triangle markers)
  // =====================================================================
  function historicalIcon() {
    return L.divIcon({
      className: 'historical-marker-fade', html: '<div style="width:0;height:0;border-left:7px solid transparent;border-right:7px solid transparent;border-bottom:13px solid #6d28d9;filter:drop-shadow(0 0 2px white);"></div>',
      iconSize: [14, 13], iconAnchor: [7, 13]
    });
  }

  function renderHistorical() {
    historicalRefs.forEach(function(m) { map.removeLayer(m); });
    historicalRefs = [];
    var show = document.getElementById('toggle-historical').checked;
    if (!show) return;

    HISTORICAL_EVENTS.forEach(function(ev) {
      var marker = L.marker([ev.latitude, ev.longitude], { icon: historicalIcon() }).addTo(map);
      marker.bindPopup(
        "<b>" + ev.name + "</b><br>" +
        "<span style='color:#6d28d9;font-weight:600;'>" + ev.date + "</span><br>" +
        ev.description + "<br>" +
        "<small style='color:#64748b;'>Source: " + ev.source + "<br>Confidence: " + ev.confidence + "</small>"
      );
      historicalRefs.push(marker);
    });
  }

  // =====================================================================
  // EXPLAINABILITY PANEL (baseline vs trigger split + ranked reasons)
  // =====================================================================
  function openExplain(area) {
    document.getElementById('explain-panel').classList.add('open');
    document.getElementById('explain-name').textContent = area.area_name;

    var color = getRiskColor(area.risk_level);
    var badge = document.getElementById('explain-badge');
    badge.textContent = area.risk_level + " — " + area.risk_score + "/100";
    badge.style.background = color;

    // Component scores (same math as backend formula — replicated here
    // for display only; source of truth remains the backend)
    var slope = Math.min((area.slope_degree||0)/60*100,100);
    var road = Math.max(0,100-Math.min((area.road_distance_m||0)/500*100,100));
    var geology = Math.min((area.geology_score||0)/10*100,100);
    var landuse = Math.min((area.landuse_score||0)/10*100,100);
    var drainage = Math.min((area.drainage_score||0)/10*100,100);
    var rainfallTrigger = Math.min((area.rainfall_24h_mm||0)/205*100,100);
    var antecedent = Math.min((area.rainfall_antecedent_mm||0)/100*100,100);
    var rainfallComponent = (rainfallTrigger*0.7)+(antecedent*0.3);

    var baselineScore = Math.round(((slope*0.20)+(road*0.15)+(geology*0.15)+(landuse*0.10)+(drainage*0.10))/0.70);
    var triggerScore = Math.round(rainfallComponent);

    function labelFor(v){ if(v>=80) return "Very High"; if(v>=60) return "High"; if(v>=35) return "Moderate"; return "Low"; }
    document.getElementById('explain-baseline').textContent = labelFor(baselineScore);
    document.getElementById('explain-trigger').textContent = labelFor(triggerScore);

    // Ranked "why high risk" — top 3 contributing factors
    var factors = [
      { label: "Steep terrain (slope)", value: slope },
      { label: "Rainfall trigger (24h + antecedent)", value: rainfallComponent },
      { label: "Close to road / road-cutting", value: road },
      { label: "Weak/fractured geology", value: geology },
      { label: "Land-use disturbance", value: landuse },
      { label: "Poor drainage / wetness", value: drainage }
    ].sort(function(a,b){ return b.value - a.value; });

    var whyHtml = "";
    factors.slice(0,3).forEach(function(f) { whyHtml += "<li>" + f.label + "</li>"; });
    document.getElementById('explain-why-list').innerHTML = whyHtml;

    var factorHtml = "";
    factors.forEach(function(f) {
      factorHtml += "<div class='factor-row'>" +
        "<div class='factor-label'><span>" + f.label + "</span><span>" + Math.round(f.value) + "%</span></div>" +
        "<div class='factor-bar-bg'><div class='factor-bar-fill' style='width:" + f.value + "%;background:" + color + "'></div></div>" +
        "</div>";
    });
    document.getElementById('explain-factors').innerHTML = factorHtml;
    document.getElementById('explain-source').innerHTML =
      "<b>Source:</b> " + (area.data_source || "Not specified") + "<br>" + timeAgo(area.last_updated);
  }
  function closeExplain() { document.getElementById('explain-panel').classList.remove('open'); }

  // =====================================================================
  // MINI STATS — count-up animation (feels alive, not a static number)
  // =====================================================================
  function animateCount(elementId, targetValue) {
    var el = document.getElementById(elementId);
    var current = parseInt(el.textContent) || 0;
    if (current === targetValue) return;
    var step = targetValue > current ? 1 : -1;
    var timer = setInterval(function() {
      current += step;
      el.textContent = current;
      if (current === targetValue) clearInterval(timer);
    }, 40);
  }

  function updateStats(areas) {
    animateCount('stat-total', areas.length);
    animateCount('stat-critical', areas.filter(function(a){return a.risk_level==='Critical';}).length);
    animateCount('stat-history', HISTORICAL_EVENTS.length);
  }

  // =====================================================================
  // CINEMATIC "PLAY HISTORY" — flies through each real event chronologically
  // =====================================================================
  var timelinePlaying = false;
  function playTimeline() {
    if (timelinePlaying) return;
    timelinePlaying = true;
    var btn = document.getElementById('play-timeline-btn');
    btn.textContent = "⏸ Playing...";

    var sortedEvents = HISTORICAL_EVENTS.slice(); // already chronological in our data
    var i = 0;

    function showNext() {
      if (i >= sortedEvents.length) {
        timelinePlaying = false;
        btn.textContent = "▶ Play History (1992–2024)";
        map.flyTo([23.7271, 92.7176], 12, { duration: 1.2 });
        return;
      }
      var ev = sortedEvents[i];
      map.flyTo([ev.latitude, ev.longitude], 15, { duration: 1.3 });
      setTimeout(function() {
        var m = historicalRefs[i];
        if (m) m.openPopup();
      }, 1350);
      i++;
      setTimeout(showNext, 3200);
    }
    showNext();
  }

  // =====================================================================
  // BACKEND SE LIVE DATA
  // =====================================================================
  function loadRiskScores() {
    fetch(BACKEND_URL + "/api/risk-scores")
      .then(function(r) { if (!r.ok) throw new Error("Server error"); return r.json(); })
      .then(function(data) {
        document.getElementById("status-pill").textContent = "🟢 Live Data";
        document.getElementById("status-pill").classList.remove("offline");
        document.getElementById("tag-backend").textContent = "LIVE";
        document.getElementById("tag-backend").className = "tag tag-live";
        var finalData = data.length ? data : FALLBACK_DATA;
        renderAreas(finalData);
        updateStats(finalData);
        checkAndLogAlerts(finalData);
      })
      .catch(function(err) {
        console.warn("Backend se connect nahi ho paya:", err);
        document.getElementById("status-pill").textContent = "🔴 Offline (Sample Data)";
        document.getElementById("status-pill").classList.add("offline");
        document.getElementById("tag-backend").textContent = "OFFLINE/DEMO";
        document.getElementById("tag-backend").className = "tag tag-demo";
        renderAreas(FALLBACK_DATA);
        updateStats(FALLBACK_DATA);
      });
  }

  loadRiskScores();
  renderHistorical();
  setInterval(loadRiskScores, 30000);

  // =====================================================================
  // REPORT HAZARD MODAL — form ab isi map page ke andar hai
  // =====================================================================
  const QUEUE_KEY = "sih_pending_reports_v1";
  var rState = {
    reporterType: "Citizen", observationType: "ground_crack", severity: "Low",
    latitude: null, longitude: null, photoBase64: null, photoName: null
  };
  var locMap = null; // lazy-init hoga jab modal pehli baar khulega

  function openReportModal() {
    document.getElementById('report-modal-overlay').classList.add('show');
    if (!locMap) {
      setTimeout(function() {
        locMap = L.map('location-map', { zoomControl: false }).setView([23.7271, 92.7176], 13);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution:'© OSM' }).addTo(locMap);
        locMap.on('click', function(e) { setReportLocation(e.latlng.lat, e.latlng.lng); });
      }, 100);
    } else {
      setTimeout(function() { locMap.invalidateSize(); }, 100);
    }
  }
  function closeReportModal() {
    document.getElementById('report-modal-overlay').classList.remove('show');
  }

  function rSelectToggle(el, key) {
    el.parentElement.querySelectorAll('.toggle-btn').forEach(function(b){ b.classList.remove('active'); });
    el.classList.add('active');
    rState[key] = el.dataset.value;
  }
  function rSelectObs(el) {
    el.parentElement.querySelectorAll('.obs-card').forEach(function(b){ b.classList.remove('active'); });
    el.classList.add('active');
    rState.observationType = el.dataset.value;
  }
  function rSelectSeverity(el) {
    el.parentElement.querySelectorAll('.sev-btn').forEach(function(b){ b.classList.remove('active'); });
    el.classList.add('active');
    rState.severity = el.dataset.value;
  }

  function setReportLocation(lat, lng) {
    rState.latitude = lat; rState.longitude = lng;
    if (window._locMarker) locMap.removeLayer(window._locMarker);
    window._locMarker = L.marker([lat, lng]).addTo(locMap);
    document.getElementById('coords-display').textContent = "📍 " + lat.toFixed(5) + ", " + lng.toFixed(5);
    document.getElementById('form-error').style.display = 'none';
  }

  function useMyLocation() {
    var btn = document.getElementById('locate-btn');
    btn.textContent = "📡 Locating...";
    if (!navigator.geolocation) {
      btn.textContent = "📡 Use My Current Location";
      alert("Geolocation not supported on this device. Please tap the mini-map instead.");
      return;
    }
    navigator.geolocation.getCurrentPosition(function(pos) {
      locMap.setView([pos.coords.latitude, pos.coords.longitude], 16);
      setReportLocation(pos.coords.latitude, pos.coords.longitude);
      btn.textContent = "📡 Use My Current Location";
    }, function() {
      btn.textContent = "📡 Use My Current Location";
      alert("Could not get location — please tap the mini-map to set it manually.");
    });
  }

  function handlePhoto(e) {
    var file = e.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function(ev) {
      rState.photoBase64 = ev.target.result;
      rState.photoName = file.name;
      document.getElementById('photo-preview-img').src = ev.target.result;
      document.getElementById('photo-preview').style.display = 'block';
      document.getElementById('photo-drop').style.display = 'none';
    };
    reader.readAsDataURL(file);
  }
  function removePhoto() {
    rState.photoBase64 = null; rState.photoName = null;
    document.getElementById('photo-preview').style.display = 'none';
    document.getElementById('photo-drop').style.display = 'block';
    document.getElementById('photo-input').value = '';
  }

  function base64ToBlob(base64) {
    var parts = base64.split(',');
    var mime = parts[0].match(/:(.*?);/)[1];
    var binary = atob(parts[1]);
    var array = new Uint8Array(binary.length);
    for (var i = 0; i < binary.length; i++) array[i] = binary.charCodeAt(i);
    return new Blob([array], { type: mime });
  }

  function getQueue() { try { return JSON.parse(localStorage.getItem(QUEUE_KEY)) || []; } catch (e) { return []; } }
  function saveQueue(q) { localStorage.setItem(QUEUE_KEY, JSON.stringify(q)); }

  function updateSyncBanner() {
    var q = getQueue();
    var banner = document.getElementById('sync-banner');
    if (q.length > 0) {
      banner.classList.add('show'); banner.classList.remove('synced');
      document.getElementById('sync-banner-text').textContent =
        "⏳ " + q.length + " report(s) waiting to sync (no internet at time of submission)";
    } else { banner.classList.remove('show'); }
  }
  function queueReport(reportData) {
    var q = getQueue(); q.push(reportData); saveQueue(q); updateSyncBanner();
  }
  function trySyncQueue() {
    var q = getQueue();
    if (q.length === 0) return;
    var remaining = [];
    var syncPromises = q.map(function(report) {
      var formData = new FormData();
      formData.append('reporter_name', report.reporter_name);
      formData.append('reporter_type', report.reporter_type);
      formData.append('latitude', report.latitude);
      formData.append('longitude', report.longitude);
      formData.append('observation_type', report.observation_type);
      formData.append('severity', report.severity);
      formData.append('description', report.description);
      if (report.photoBase64) formData.append('photo', base64ToBlob(report.photoBase64), report.photoName || 'photo.jpg');
      return fetch(BACKEND_URL + "/api/reports", { method: 'POST', body: formData })
        .then(function(r) { return r.ok; }).catch(function() { return false; })
        .then(function(ok) { if (!ok) remaining.push(report); });
    });
    Promise.all(syncPromises).then(function() {
      saveQueue(remaining); updateSyncBanner();
      if (remaining.length === 0 && q.length > 0) {
        var banner = document.getElementById('sync-banner');
        banner.classList.add('show', 'synced');
        document.getElementById('sync-banner-text').textContent = "✅ All queued reports synced!";
        setTimeout(function() { banner.classList.remove('show'); }, 3000);
      }
    });
  }
  window.addEventListener('online', trySyncQueue);

  function submitReport() {
    if (rState.latitude === null) {
      document.getElementById('form-error').style.display = 'block';
      return;
    }
    var reportData = {
      reporter_name: document.getElementById('reporter-name').value || "Anonymous",
      reporter_type: rState.reporterType, latitude: rState.latitude, longitude: rState.longitude,
      observation_type: rState.observationType, severity: rState.severity,
      description: document.getElementById('report-description').value || "",
      photoBase64: rState.photoBase64, photoName: rState.photoName
    };

    var btn = document.getElementById('report-submit-btn');
    btn.disabled = true;
    document.getElementById('submit-spinner').style.display = 'inline-block';
    document.getElementById('submit-btn-text').textContent = "Submitting...";

    if (!navigator.onLine) {
      queueReport(reportData);
      showReportSuccess(true, "No internet connection right now. Your report is saved on this device and will upload automatically once you're back online.");
      resetReportForm();
      return;
    }

    var formData = new FormData();
    formData.append('reporter_name', reportData.reporter_name);
    formData.append('reporter_type', reportData.reporter_type);
    formData.append('latitude', reportData.latitude);
    formData.append('longitude', reportData.longitude);
    formData.append('observation_type', reportData.observation_type);
    formData.append('severity', reportData.severity);
    formData.append('description', reportData.description);
    if (reportData.photoBase64) formData.append('photo', base64ToBlob(reportData.photoBase64), reportData.photoName || 'photo.jpg');

    fetch(BACKEND_URL + "/api/reports", { method: 'POST', body: formData })
      .then(function(r) { if (!r.ok) throw new Error("Server error"); return r.json(); })
      .then(function(result) {
        if (result.status === 'duplicate_flagged') {
          showReportSuccess(false, "A similar report was already submitted recently from this location — thank you for confirming it.", true);
        } else {
          showReportSuccess(false, "Your report has been received and will be reviewed by the response team.");
        }
        resetReportForm();
      })
      .catch(function() {
        queueReport(reportData);
        showReportSuccess(true, "Could not reach the server right now. Your report is saved on this device and will upload automatically once connection is restored.");
        resetReportForm();
      });
  }

  function showReportSuccess(isOffline, message, isDuplicate) {
    document.getElementById('report-submit-btn').disabled = false;
    document.getElementById('submit-spinner').style.display = 'none';
    document.getElementById('submit-btn-text').textContent = "Submit Report";
    closeReportModal();

    var icon = document.getElementById('success-icon');
    var title = document.getElementById('success-title');
    var badge = document.getElementById('success-status-badge');
    icon.className = 'success-icon';

    if (isOffline) {
      icon.classList.add('offline'); icon.textContent = "📥";
      title.textContent = "Saved Offline"; badge.textContent = "QUEUED FOR SYNC";
      badge.style.background = "#fef3c7"; badge.style.color = "#92400e";
    } else if (isDuplicate) {
      icon.textContent = "🔁"; title.textContent = "Already Reported"; badge.textContent = "DUPLICATE FLAGGED";
      badge.style.background = "#e0e7ff"; badge.style.color = "#3730a3";
    } else {
      icon.textContent = "✓"; title.textContent = "Report Submitted"; badge.textContent = "PENDING VERIFICATION";
      badge.style.background = "#fef3c7"; badge.style.color = "#92400e";
    }
    document.getElementById('success-message').textContent = message;
    document.getElementById('success-overlay').classList.add('show');
    updateSyncBanner();
  }
  function closeSuccess() { document.getElementById('success-overlay').classList.remove('show'); }
  function resetReportForm() {
    document.getElementById('reporter-name').value = '';
    document.getElementById('report-description').value = '';
    removePhoto();
  }

  updateSyncBanner();
  if (navigator.onLine) trySyncQueue();

  // =====================================================================
  // ALERT SIMULATION LOG
  // (Real SIH requirement: "automated alerts to authorities/communities".
  //  We don't have a real SMS gateway/budget, so this SIMULATES the alert
  //  trigger + recipient logic honestly — clearly labeled as simulated.)
  // =====================================================================
  var alertLog = [];
  var previousLevels = {};

  function checkAndLogAlerts(areas) {
    var newAlerts = 0;
    areas.forEach(function(area) {
      var prev = previousLevels[area.area_name];
      if ((area.risk_level === 'Critical' || area.risk_level === 'High') && prev !== area.risk_level) {
        alertLog.unshift({
          time: new Date(),
          area: area.area_name,
          level: area.risk_level,
          score: area.risk_score
        });
        if (alertLog.length > 25) alertLog.pop();
        newAlerts++;
      }
      previousLevels[area.area_name] = area.risk_level;
    });
    if (newAlerts > 0) renderAlertLog();
  }

  function renderAlertLog() {
    var badge = document.getElementById('alert-badge');
    badge.textContent = alertLog.length > 0 ? alertLog.length : "";

    var listEl = document.getElementById('alert-log-list');
    if (alertLog.length === 0) {
      listEl.innerHTML = "<div class='no-results'>No alerts yet — alerts appear when an area's risk becomes High or Critical.</div>";
      return;
    }
    var html = "";
    alertLog.forEach(function(a) {
      var cls = a.level === 'Critical' ? '' : 'high';
      html += "<div class='alert-entry " + cls + "'>" +
        "<div class='alert-time'>" + a.time.toLocaleTimeString() + "</div>" +
        "<div class='alert-title'>" + a.level.toUpperCase() + " — " + a.area + " (" + a.score + "/100)</div>" +
        "<div class='alert-recipients'>📨 Simulated SMS/app notification sent to: District Disaster Management Authority, local Village Council</div>" +
        "</div>";
    });
    listEl.innerHTML = html;
  }

  function toggleAlertLog() {
    document.getElementById('alert-log-panel').classList.toggle('open');
  }

  // =====================================================================
  // LANGUAGE TOGGLE (English / Hindi)
  // NOTE: Mizo (the local language for Aizawl) is NOT included here —
  // machine-translating technical dashboard terms into Mizo without a
  // native speaker risks incorrect/embarrassing phrasing. VERIFY REQUIRED:
  // get a Mizo-speaking team member or local contact to review before
  // adding a Mizo option.
  // =====================================================================
  var currentLang = 'en';
  var translations = {
    en: {
      title: "🏔️ Aizawl Landslide Risk Map", subtitle: "SIH26001 — MDoNER Early Warning System",
      reportBtn: "📍 Report Hazard", playBtn: "▶ Play History (1992–2024)", areasBtn: "☰ Areas", fullscreenBtn: "⛶ Fullscreen",
      searchPlaceholder: "Search area name...", layerLive: "Current Risk Areas (live)", layerHistorical: "Historical Events (research)",
      filterAll: "All", filterLow: "Low", filterModerate: "Moderate", filterHigh: "High", filterCritical: "Critical",
      areasLabel: "AREAS (click for details)", legendTitle: "Risk Level", legendHistorical: "Historical event",
      statusTitle: "System / Data Status", statTotal: "Areas Monitored", statCritical: "Critical Now", statHistory: "Historical Events"
    },
    hi: {
      title: "🏔️ आइज़ोल भूस्खलन जोखिम मानचित्र", subtitle: "SIH26001 — MDoNER पूर्व चेतावनी प्रणाली",
      reportBtn: "📍 खतरे की सूचना दें", playBtn: "▶ इतिहास चलाएं (1992–2024)", areasBtn: "☰ क्षेत्र", fullscreenBtn: "⛶ पूर्ण स्क्रीन",
      searchPlaceholder: "क्षेत्र का नाम खोजें...", layerLive: "वर्तमान जोखिम क्षेत्र (लाइव)", layerHistorical: "ऐतिहासिक घटनाएं (शोध)",
      filterAll: "सभी", filterLow: "कम", filterModerate: "मध्यम", filterHigh: "उच्च", filterCritical: "गंभीर",
      areasLabel: "क्षेत्र (विवरण के लिए क्लिक करें)", legendTitle: "जोखिम स्तर", legendHistorical: "ऐतिहासिक घटना",
      statusTitle: "सिस्टम / डेटा स्थिति", statTotal: "निगरानी क्षेत्र", statCritical: "अभी गंभीर", statHistory: "ऐतिहासिक घटनाएं"
    }
  };

  function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'hi' : 'en';
    applyLanguage();
  }

  function applyLanguage() {
    var t = translations[currentLang];
    document.getElementById('lang-toggle-btn').textContent = currentLang === 'en' ? "🌐 EN" : "🌐 हिं";
    document.querySelector('#topbar h1').textContent = t.title;
    document.querySelector('#topbar .subtitle').textContent = t.subtitle;
    document.getElementById('report-hazard-btn').textContent = t.reportBtn;
    document.getElementById('play-timeline-btn').textContent = timelinePlaying ? document.getElementById('play-timeline-btn').textContent : t.playBtn;
    document.getElementById('mobile-toggle').textContent = t.areasBtn;
    document.getElementById('search-input').placeholder = t.searchPlaceholder;
    var layerLabels = document.querySelectorAll('#layer-toggles label');
    layerLabels[0].lastChild.textContent = " " + t.layerLive;
    layerLabels[1].lastChild.textContent = " " + t.layerHistorical;
    document.querySelector('[data-level="All"]').textContent = t.filterAll;
    document.querySelector('[data-level="Low"]').textContent = t.filterLow;
    document.querySelector('[data-level="Moderate"]').textContent = t.filterModerate;
    document.querySelector('[data-level="High"]').textContent = t.filterHigh;
    document.querySelector('[data-level="Critical"]').textContent = t.filterCritical;
    document.getElementById('area-list-label').textContent = t.areasLabel;
    document.querySelector('.legend b').textContent = t.legendTitle;
    document.getElementById('status-panel').querySelector('b').textContent = t.statusTitle;
    document.querySelector('.stat-box:nth-child(1) .stat-label').textContent = t.statTotal;
    document.querySelector('.stat-box:nth-child(2) .stat-label').textContent = t.statCritical;
    document.querySelector('.stat-box:nth-child(3) .stat-label').textContent = t.statHistory;
  }

  // =====================================================================
  // AUTH — Login/Signup for Field Officers & Authorities
  // (Prototype-level: hashed passwords server-side, signed tokens.
  //  Right now this only demonstrates login/signup working end-to-end;
  //  it isn't yet wired to a full authority-review dashboard — that is
  //  a separate, larger piece of work.)
  // =====================================================================
  var authTab = 'login';
  var authRole = 'field_officer';
  const AUTH_TOKEN_KEY = 'sih_auth_token';

  function setAuthRole(el) {
    el.parentElement.querySelectorAll('.toggle-btn').forEach(function(b){ b.classList.remove('active'); });
    el.classList.add('active');
    authRole = el.dataset.value;
  }

  function setAuthTab(tab, el) {
    authTab = tab;
    document.querySelectorAll('.auth-tab').forEach(function(t){ t.classList.remove('active'); });
    el.classList.add('active');
    document.getElementById('auth-role-group').style.display = tab === 'signup' ? 'block' : 'none';
    document.getElementById('auth-submit-text').textContent = tab === 'signup' ? 'Create Account' : 'Login';
    document.getElementById('auth-error').style.display = 'none';
  }

  function openAuthModal() {
    document.getElementById('auth-modal-overlay').classList.add('show');
    refreshAuthUI();
  }
  function closeAuthModal() { document.getElementById('auth-modal-overlay').classList.remove('show'); }

  function getAuthToken() { return localStorage.getItem(AUTH_TOKEN_KEY); }

  function refreshAuthUI() {
    var token = getAuthToken();
    var savedUser = localStorage.getItem('sih_auth_user');
    var savedRole = localStorage.getItem('sih_auth_role');
    var loggedInView = document.getElementById('auth-loggedin-view');
    var formFields = document.querySelectorAll('#auth-modal-card .field-group, .auth-tabs, #auth-submit-btn');

    if (token && savedUser) {
      loggedInView.style.display = 'block';
      formFields.forEach(function(f){ f.style.display = 'none'; });
      document.getElementById('auth-loggedin-name').textContent = savedUser;
      document.getElementById('auth-loggedin-role').textContent = savedRole === 'authority' ? '🏛️ Authority' : '🦺 Field Officer';
      document.getElementById('auth-btn').textContent = "👤 " + savedUser;
    } else {
      loggedInView.style.display = 'none';
      formFields.forEach(function(f){ f.style.display = ''; });
      document.getElementById('auth-role-group').style.display = authTab === 'signup' ? 'block' : 'none';
      document.getElementById('auth-btn').textContent = "🔑 Login";
    }
  }

  function submitAuth() {
    var username = document.getElementById('auth-username').value.trim();
    var password = document.getElementById('auth-password').value;
    var errorEl = document.getElementById('auth-error');
    errorEl.style.display = 'none';

    if (username.length < 3 || password.length < 6) {
      errorEl.textContent = "Username must be 3+ chars, password 6+ chars.";
      errorEl.style.display = 'block';
      return;
    }

    var btn = document.getElementById('auth-submit-btn');
    btn.disabled = true;
    document.getElementById('auth-spinner').style.display = 'inline-block';

    var endpoint = authTab === 'signup' ? '/api/auth/signup' : '/api/auth/login';
    var body = authTab === 'signup'
      ? { username: username, password: password, role: authRole }
      : { username: username, password: password };

    fetch(BACKEND_URL + endpoint, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    })
      .then(function(r) { return r.json().then(function(data) { return { ok: r.ok, data: data }; }); })
      .then(function(result) {
        btn.disabled = false;
        document.getElementById('auth-spinner').style.display = 'none';
        if (!result.ok) {
          errorEl.textContent = result.data.error || "Something went wrong.";
          errorEl.style.display = 'block';
          return;
        }
        if (authTab === 'signup') {
          errorEl.style.display = 'none';
          setAuthTab('login', document.querySelector('.auth-tab'));
          alert("Account created! Please log in now.");
        } else {
          localStorage.setItem(AUTH_TOKEN_KEY, result.data.token);
          localStorage.setItem('sih_auth_user', result.data.username);
          localStorage.setItem('sih_auth_role', result.data.role);
          refreshAuthUI();
        }
      })
      .catch(function() {
        btn.disabled = false;
        document.getElementById('auth-spinner').style.display = 'none';
        errorEl.textContent = "Could not reach server. Check your connection.";
        errorEl.style.display = 'block';
      });
  }

  function logout() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem('sih_auth_user');
    localStorage.removeItem('sih_auth_role');
    refreshAuthUI();
    closeAuthModal();
  }

  refreshAuthUI();
</script>
  <!-- ===================================================================
       REPORT HAZARD MODAL — map aur report form ab EK hi jagah hain
       =================================================================== -->
  <div id="report-modal-overlay">
    <div id="report-modal-card">
      <div id="report-modal-header">
        <div>
          <h2>📍 Report a Hazard</h2>
          <div class="report-subtitle">Ground crack, slope movement, road damage — help us verify it</div>
        </div>
        <button id="report-modal-close" onclick="closeReportModal()">✕</button>
      </div>

      <div id="report-modal-body">
        <div class="field-group" style="animation-delay:0.02s">
          <div class="field-label">Who are you reporting as? <span class="required-star">*</span></div>
          <div class="toggle-row">
            <div class="toggle-btn active" data-value="Citizen" onclick="rSelectToggle(this,'reporterType')">👤 Citizen</div>
            <div class="toggle-btn" data-value="Field Officer" onclick="rSelectToggle(this,'reporterType')">🦺 Field Officer</div>
          </div>
        </div>

        <div class="field-group" style="animation-delay:0.06s">
          <div class="field-label">Your Name (optional)</div>
          <input type="text" id="reporter-name" placeholder="e.g. Ramdinthara">
        </div>

        <div class="field-group" style="animation-delay:0.10s">
          <div class="field-label">What did you observe? <span class="required-star">*</span></div>
          <div class="obs-grid">
            <div class="obs-card active" data-value="ground_crack" onclick="rSelectObs(this)"><span class="obs-icon">🪨</span>Ground crack</div>
            <div class="obs-card" data-value="slope_movement" onclick="rSelectObs(this)"><span class="obs-icon">⛰️</span>Slope movement</div>
            <div class="obs-card" data-value="rockfall" onclick="rSelectObs(this)"><span class="obs-icon">🧱</span>Rockfall</div>
            <div class="obs-card" data-value="drainage_issue" onclick="rSelectObs(this)"><span class="obs-icon">💧</span>Drainage issue</div>
            <div class="obs-card" data-value="road_damage" onclick="rSelectObs(this)"><span class="obs-icon">🛣️</span>Road damage</div>
            <div class="obs-card" data-value="other" onclick="rSelectObs(this)"><span class="obs-icon">❓</span>Other</div>
          </div>
        </div>

        <div class="field-group" style="animation-delay:0.14s">
          <div class="field-label">Severity (your estimate) <span class="required-star">*</span></div>
          <div class="severity-row">
            <button type="button" class="sev-btn sev-low active" data-value="Low" onclick="rSelectSeverity(this)">Low</button>
            <button type="button" class="sev-btn sev-medium" data-value="Medium" onclick="rSelectSeverity(this)">Medium</button>
            <button type="button" class="sev-btn sev-high" data-value="High" onclick="rSelectSeverity(this)">High</button>
          </div>
        </div>

        <div class="field-group" style="animation-delay:0.18s">
          <div class="field-label">Description</div>
          <textarea id="report-description" placeholder="e.g. Fresh crack appeared near the road, about 2 feet long..."></textarea>
        </div>

        <div class="field-group" style="animation-delay:0.22s">
          <div class="field-label">Location <span class="required-star">*</span></div>
          <button type="button" id="locate-btn" onclick="useMyLocation()">📡 Use My Current Location</button>
          <div id="location-map"></div>
          <div id="coords-display">Tap on the mini-map, or use the button above, to set location</div>
        </div>

        <div class="field-group" style="animation-delay:0.26s">
          <div class="field-label">Photo (optional but recommended)</div>
          <div id="photo-drop" onclick="document.getElementById('photo-input').click()">📷 Tap to add a photo</div>
          <input type="file" id="photo-input" accept="image/*" capture="environment" style="display:none" onchange="handlePhoto(event)">
          <div id="photo-preview">
            <img id="photo-preview-img" src="">
            <span class="remove-photo" onclick="removePhoto()">Remove photo</span>
          </div>
        </div>

        <div class="error-text" id="form-error">Please select a location before submitting.</div>

        <button id="report-submit-btn" onclick="submitReport()">
          <span class="spinner" id="submit-spinner"></span>
          <span id="submit-btn-text">Submit Report</span>
        </button>
      </div>
    </div>
  </div>

  <div id="success-overlay">
    <div id="success-card">
      <div class="success-icon" id="success-icon">✓</div>
      <h3 id="success-title" style="margin:0 0 6px 0;">Report Submitted</h3>
      <p id="success-message" style="font-size:13px; color:#64748b; margin:0;">Thank you — your report has been received.</p>
      <div id="success-status-badge">PENDING VERIFICATION</div>
      <br>
      <button onclick="closeSuccess()">Done</button>
    </div>
  </div>

  <!-- ===================================================================
       LOGIN / SIGNUP MODAL — Field Officers / Authorities ke liye
       =================================================================== -->
  <div id="auth-modal-overlay">
    <div id="auth-modal-card">
      <button class="report-modal-close" id="auth-modal-close" onclick="closeAuthModal()">✕</button>
      <h3 id="auth-modal-title">Field Officer / Authority Login</h3>
      <div class="auth-tabs">
        <div class="auth-tab active" onclick="setAuthTab('login', this)">Login</div>
        <div class="auth-tab" onclick="setAuthTab('signup', this)">Sign Up</div>
      </div>

      <div id="auth-error" class="error-text"></div>

      <div class="field-group">
        <div class="field-label">Username</div>
        <input type="text" id="auth-username" placeholder="e.g. officer_aizawl">
      </div>
      <div class="field-group">
        <div class="field-label">Password</div>
        <input type="text" id="auth-password" placeholder="At least 6 characters">
      </div>
      <div class="field-group" id="auth-role-group">
        <div class="field-label">Role</div>
        <div class="toggle-row">
          <div class="toggle-btn active" data-value="field_officer" onclick="setAuthRole(this)">🦺 Field Officer</div>
          <div class="toggle-btn" data-value="authority" onclick="setAuthRole(this)">🏛️ Authority</div>
        </div>
      </div>

      <button id="auth-submit-btn" onclick="submitAuth()">
        <span class="spinner" id="auth-spinner"></span>
        <span id="auth-submit-text">Login</span>
      </button>

      <div id="auth-loggedin-view" style="display:none; text-align:center; padding:10px 0;">
        <div style="font-size:14px; font-weight:600;">👤 <span id="auth-loggedin-name"></span></div>
        <div style="font-size:11.5px; color:#64748b; margin:4px 0 14px 0;" id="auth-loggedin-role"></div>
        <button onclick="logout()" style="background:#ef4444; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer;">Logout</button>
      </div>
    </div>
  </div>

</body>
</html>
