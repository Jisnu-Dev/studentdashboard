"use client";

const PRESETS = ["50", "100"];

// Maximum marks of each periodical test: quick presets plus any other number.
export default function MaxMarksField({ value, onChange }) {
  return (
    <div className="form-group">
      <label className="form-label">Maximum Marks (PT I and PT II are out of)</label>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        {PRESETS.map((preset) => (
          <button key={preset} type="button" className="btn btn-ghost btn-sm" onClick={() => onChange(preset)}
            style={String(value) === preset
              ? { color: "var(--accent)", borderColor: "var(--accent)", background: "var(--accent-bg)" }
              : {}}>
            {preset}
          </button>
        ))}
        <input className="form-input" type="number" min="1" max="1000" step="1" required
          value={value} onChange={(e) => onChange(e.target.value)}
          style={{ width: 110 }} aria-label="Maximum marks" />
        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>or type any other maximum</span>
      </div>
    </div>
  );
}
