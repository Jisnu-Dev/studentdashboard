"use client";
import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ai, batches, students as studentsApi } from "@/lib/api";
import { Bot, BarChart2, Calendar, MessageSquare, User, Trash2, Send, RotateCcw, Sparkles } from "@/lib/icons";

// ── Simple Markdown renderer ──────────────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return [];
  const lines = text.split("\n");
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("### ")) {
      elements.push(<h4 key={i} style={{ color: "var(--accent)", fontWeight: 700, marginTop: 18, marginBottom: 6, fontSize: "0.95rem" }}>{applyInline(line.slice(4))}</h4>);
    } else if (line.startsWith("## ")) {
      elements.push(<h3 key={i} style={{ color: "var(--accent)", fontWeight: 800, marginTop: 22, marginBottom: 8, fontSize: "1.05rem" }}>{applyInline(line.slice(3))}</h3>);
    } else if (line.startsWith("# ")) {
      elements.push(<h2 key={i} style={{ color: "var(--accent)", fontWeight: 800, marginTop: 24, marginBottom: 10, fontSize: "1.15rem" }}>{applyInline(line.slice(2))}</h2>);
    } else if (line.startsWith("**") && line.endsWith("**") && line.length > 4) {
      elements.push(<p key={i} style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>{applyInline(line)}</p>);
    } else if (line.startsWith("- ") || line.startsWith("* ")) {
      elements.push(
        <div key={i} style={{ display: "flex", gap: 10, marginBottom: 5, paddingLeft: 8 }}>
          <span style={{ color: "var(--accent)", flexShrink: 0, marginTop: 2 }}>•</span>
          <span style={{ color: "var(--text-secondary)", lineHeight: 1.6 }}>{applyInline(line.slice(2))}</span>
        </div>
      );
    } else if (/^\d+\.\s/.test(line)) {
      const num = line.match(/^(\d+)\./)[1];
      elements.push(
        <div key={i} style={{ display: "flex", gap: 10, marginBottom: 5, paddingLeft: 8 }}>
          <span style={{ color: "var(--warning)", flexShrink: 0, fontWeight: 700, minWidth: 20 }}>{num}.</span>
          <span style={{ color: "var(--text-secondary)", lineHeight: 1.6 }}>{applyInline(line.replace(/^\d+\.\s/, ""))}</span>
        </div>
      );
    } else if (line.trim() === "" || line.trim() === "---") {
      elements.push(<div key={i} style={{ height: 8 }} />);
    } else if (line.trim()) {
      elements.push(<p key={i} style={{ color: "var(--text-secondary)", marginBottom: 6, lineHeight: 1.7 }}>{applyInline(line)}</p>);
    }
    i++;
  }
  return elements;
}

function applyInline(text) {
  // Bold: **text**
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} style={{ color: "var(--text-primary)", fontWeight: 700 }}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

// ── Structured report / schedule renderers ─────────────────────────────────────
function Bullets({ items, color = "var(--accent)" }) {
  if (!items?.length) return null;
  return (
    <div style={{ marginBottom: 14 }}>
      {items.map((item, i) => (
        <div key={i} style={{ display: "flex", gap: 10, marginBottom: 6, paddingLeft: 4 }}>
          <span style={{ color, flexShrink: 0, marginTop: 2 }}>•</span>
          <span style={{ color: "var(--text-secondary)", lineHeight: 1.6 }}>{item}</span>
        </div>
      ))}
    </div>
  );
}

function Section({ title, children }) {
  if (!children) return null;
  return (
    <div style={{ marginBottom: 20 }}>
      <h4 style={{ color: "var(--accent)", fontWeight: 700, marginBottom: 8, fontSize: "0.9rem" }}>{title}</h4>
      {children}
    </div>
  );
}

const PRIORITY_COLOR = { High: "var(--danger)", Medium: "var(--warning)", Low: "var(--success)" };

function ReportView({ data }) {
  if (!data) return null;
  return (
    <div>
      <p style={{ color: "var(--text-primary)", lineHeight: 1.7, marginBottom: 20, fontSize: "0.95rem" }}>
        {data.summary}
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <Section title="Strengths"><Bullets items={data.strengths} color="var(--success)" /></Section>
        <Section title="Concerns"><Bullets items={data.concerns} color="var(--danger)" /></Section>
      </div>

      {data.subjects?.length > 0 && (
        <Section title="Subject Breakdown">
          {data.subjects.map((s, i) => (
            <div key={i} className="card" style={{ padding: 14, marginBottom: 10, background: "var(--surface-muted)" }}>
              <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
                <span className="badge badge-purple">{s.code}</span>
              </div>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.86rem", marginBottom: 4 }}>{s.observation}</p>
              {s.action && <p style={{ color: "var(--text-primary)", fontSize: "0.86rem", fontWeight: 600 }}>→ {s.action}</p>}
            </div>
          ))}
        </Section>
      )}

      {data.recommendations?.length > 0 && (
        <Section title="Recommendations">
          {data.recommendations.map((r, i) => (
            <div key={i} style={{ display: "flex", gap: 10, marginBottom: 10, alignItems: "flex-start" }}>
              <span style={{
                fontSize: "0.7rem", fontWeight: 700, padding: "2px 8px", borderRadius: 6, flexShrink: 0,
                color: PRIORITY_COLOR[r.priority] || "var(--text-muted)",
                border: `1px solid ${PRIORITY_COLOR[r.priority] || "var(--glass-border)"}`,
              }}>{r.priority}</span>
              <div>
                <div style={{ fontWeight: 700, color: "var(--text-primary)", fontSize: "0.88rem" }}>{r.title}</div>
                <div style={{ color: "var(--text-secondary)", fontSize: "0.86rem", lineHeight: 1.6 }}>{r.detail}</div>
              </div>
            </div>
          ))}
        </Section>
      )}

      <Section title="Talking Points for Parents"><Bullets items={data.parent_talking_points} /></Section>

      {data.encouragement && (
        <div style={{
          padding: "14px 18px", borderRadius: 12, background: "var(--accent-bg)",
          border: "1px solid var(--accent-border)", color: "var(--text-primary)",
          fontSize: "0.88rem", lineHeight: 1.6,
        }}>{data.encouragement}</div>
      )}
    </div>
  );
}

function ScheduleView({ data }) {
  if (!data) return null;
  return (
    <div>
      {data.overview && (
        <p style={{ color: "var(--text-primary)", lineHeight: 1.7, marginBottom: 20, fontSize: "0.95rem" }}>
          {data.overview}
        </p>
      )}

      {data.priorities?.length > 0 && (
        <Section title="Priority Subjects">
          {data.priorities.map((p, i) => (
            <div key={i} style={{ display: "flex", gap: 10, marginBottom: 6 }}>
              <span className="badge badge-purple">{p.subject}</span>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.86rem" }}>{p.reason}</span>
            </div>
          ))}
        </Section>
      )}

      {data.week?.length > 0 && (
        <Section title="Weekly Plan">
          <div style={{ display: "grid", gap: 10 }}>
            {data.week.map((day, i) => (
              <div key={i} className="card" style={{ padding: 14, background: "var(--surface-muted)" }}>
                <div style={{ fontWeight: 700, color: "var(--success)", fontSize: "0.86rem", marginBottom: 8 }}>{day.day}</div>
                {day.blocks?.map((b, j) => (
                  <div key={j} style={{ display: "flex", gap: 10, marginBottom: 4, fontSize: "0.84rem" }}>
                    <span style={{ color: "var(--text-muted)", flexShrink: 0, minWidth: 130 }}>{b.time}</span>
                    <span className="badge badge-purple" style={{ flexShrink: 0 }}>{b.subject}</span>
                    <span style={{ color: "var(--text-secondary)" }}>{b.task}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </Section>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <Section title="Techniques"><Bullets items={data.techniques} color="var(--success)" /></Section>
        <Section title="Weekly Goals"><Bullets items={data.weekly_goals} /></Section>
      </div>
    </div>
  );
}

// ── Chat bubble ───────────────────────────────────────────────────────────────
function ChatBubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      marginBottom: 16,
      gap: 10,
      alignItems: "flex-start",
    }}>
      {!isUser && (
        <div style={{
          width: 36, height: 36, borderRadius: "50%", flexShrink: 0,
          background: "var(--accent)",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}><Bot size={18} color="#fff" strokeWidth={1.8} /></div>
      )}
      <div style={{
        maxWidth: "78%",
        padding: "12px 16px",
        borderRadius: isUser ? "16px 4px 16px 16px" : "4px 16px 16px 16px",
        background: isUser
          ? "var(--accent-bg)"
          : "var(--surface-muted)",
        border: `1px solid ${isUser ? "var(--accent-border)" : "var(--glass-border)"}`,
        lineHeight: 1.6,
      }}>
        {isUser
          ? <p style={{ color: "var(--text-primary)", margin: 0, fontSize: "0.88rem" }}>{msg.content}</p>
          : <div style={{ fontSize: "0.88rem" }}>{renderMarkdown(msg.content)}</div>
        }
      </div>
      {isUser && (
        <div style={{
          width: 36, height: 36, borderRadius: "50%", flexShrink: 0,
          background: "var(--warning-bg)", border: "1px solid var(--warning-border)",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}><User size={18} style={{ color: "var(--warning)" }} strokeWidth={1.8} /></div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function StudentAIPage() {
  const { id: batchId, studentId } = useParams();
  const router = useRouter();

  const [batch, setBatch] = useState(null);
  const [student, setStudent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("analysis");  // "analysis" | "chat"

  // Analysis state
  const [reportLoading, setReportLoading] = useState(false);
  const [scheduleLoading, setScheduleLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [analysisError, setAnalysisError] = useState("");

  // Chat state
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    Promise.all([batches.get(batchId), studentsApi.list(batchId), ai.overview(batchId, studentId)])
      .then(([b, studs, overview]) => {
        setBatch(b);
        setStudent(studs.find(s => s.id === parseInt(studentId)));
        if (overview.report) setReport(overview.report.content);
        if (overview.schedule) setSchedule(overview.schedule.content);
      })
      .finally(() => setLoading(false));
  }, [batchId, studentId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chatLoading]);

  async function handleReport() {
    setReportLoading(true); setAnalysisError(""); setReport(null);
    try {
      const res = await ai.report(batchId, studentId);
      setReport(res.content);
    } catch (e) { setAnalysisError(e.message); }
    finally { setReportLoading(false); }
  }

  async function handleSchedule() {
    setScheduleLoading(true); setAnalysisError(""); setSchedule(null);
    try {
      const res = await ai.schedule(batchId, studentId);
      setSchedule(res.content);
    } catch (e) { setAnalysisError(e.message); }
    finally { setScheduleLoading(false); }
  }

  async function handleSend(e) {
    e?.preventDefault();
    const msg = input.trim();
    if (!msg || chatLoading) return;
    setInput("");
    setChatError("");

    const newMessages = [...messages, { role: "user", content: msg }];
    setMessages(newMessages);
    setChatLoading(true);

    try {
      // Pass history excluding the last user message (it's the current message)
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const res = await ai.chat(batchId, studentId, msg, history);
      setMessages([...newMessages, { role: "model", content: res.text }]);
    } catch (e) {
      setChatError(e.message);
      setMessages(newMessages);  // keep user message, just show error
    } finally {
      setChatLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  }

  if (loading) return (
    <div style={{ display: "flex", justifyContent: "center", padding: 80 }}>
      <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
    </div>
  );

  const TABS = [
    { key: "analysis", Icon: BarChart2,    label: "Analysis & Reports" },
    { key: "chat",     Icon: MessageSquare, label: "Chat with AI" },
  ];

  return (
    <>
      {/* Header */}
      <div className="page-header">
        <div>
          <div className="breadcrumb">
            <Link href="/dashboard"><span>Dashboard</span></Link>
            <span className="sep">›</span>
            <Link href={`/dashboard/batches/${batchId}`}><span>{batch?.batch_year}</span></Link>
            <span className="sep">›</span>
            <span className="current">AI Assistant</span>
          </div>
          <h1>AI <span className="gradient-text">Assistant</span></h1>
          {student && (
            <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 6, flexWrap: "wrap" }}>
              <span style={{ color: "var(--text-secondary)" }}>{student.name}</span>
              <span className="badge badge-purple">{student.register_number}</span>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                Dept of {batch?.department}
              </span>
            </div>
          )}
        </div>
        {tab === "chat" && messages.length > 0 && (
          <button className="btn btn-ghost btn-sm"
            style={{ color: "var(--danger)", borderColor: "var(--danger-border)" }}
            onClick={() => { setMessages([]); setChatError(""); }}>
            <Trash2 size={14} strokeWidth={1.8} /> Clear Chat
          </button>
        )}
      </div>

      {/* Intro banner */}
      <div className="card" style={{
        padding: "18px 24px", marginBottom: 24,
        background: "var(--accent-bg)",
        border: "1px solid var(--accent-border)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
          <Bot size={16} style={{ color: "var(--accent)" }} strokeWidth={1.8} />
          <span style={{ color: "var(--accent)", fontWeight: 700, fontSize: "0.88rem" }}>Gemini 3.5 Flash Lite</span>
        </div>
        <p style={{ fontSize: "0.88rem", color: "var(--text-secondary)", margin: 0 }}>
          Has access to <strong style={{ color: "var(--text-primary)" }}>{student?.name}</strong>'s complete profile —
          exam marks, meeting attendance, counseling sessions and more.
          Generate AI-powered reports and study schedules, or chat freely about this student.
        </p>
      </div>

      {/* Tab switcher */}
      <div style={{
        display: "flex", gap: 4, marginBottom: 24,
        background: "var(--glass-bg)", border: "1px solid var(--glass-border)",
        borderRadius: 12, padding: 5, width: "fit-content",
      }}>
        {TABS.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            style={{
              padding: "10px 24px", borderRadius: 9, border: "none", cursor: "pointer",
              fontWeight: tab === t.key ? 700 : 500, fontSize: "0.88rem", transition: "all 0.2s",
              background: tab === t.key ? "var(--accent)" : "transparent",
              color: tab === t.key ? "#fff" : "var(--text-secondary)",
              boxShadow: tab === t.key ? "0 4px 12px var(--accent-border)" : "none",
              display: "flex", alignItems: "center", gap: 8,
            }}>
            <t.Icon size={15} strokeWidth={1.8} />
            {t.label}
          </button>
        ))}
      </div>

      {/* ── ANALYSIS TAB ─────────────────────────────────────────────────── */}
      {tab === "analysis" && (
        <div>
          {analysisError && (
            <div className="alert alert-error" style={{ marginBottom: 20 }}>{analysisError}</div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
            {/* Report card */}
            <div className="card" style={{ padding: 24 }}>
              <div style={{ marginBottom: 16 }}>
                <h3 style={{ fontSize: "1rem", marginBottom: 6 }}>Performance Report</h3>
                <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                  Comprehensive analysis of marks trends, attendance, and personalised improvement recommendations.
                </p>
              </div>
              <button className="btn btn-primary" style={{ width: "100%" }}
                onClick={handleReport} disabled={reportLoading}>
                {reportLoading
                  ? <><span className="spinner" style={{ marginRight: 8 }} />Analyzing…</>
                  : <><BarChart2 size={15} strokeWidth={1.8} /> Generate Report</>}
              </button>
            </div>

            {/* Schedule card */}
            <div className="card" style={{ padding: 24 }}>
              <div style={{ marginBottom: 16 }}>
                <h3 style={{ fontSize: "1rem", marginBottom: 6 }}>Study Schedule</h3>
                <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                  Personalised weekly study timetable based on weak subjects and upcoming exams.
                </p>
              </div>
              <button className="btn btn-primary" style={{ width: "100%",
                background: "var(--success)" }}
                onClick={handleSchedule} disabled={scheduleLoading}>
                {scheduleLoading
                  ? <><span className="spinner" style={{ marginRight: 8 }} />Planning…</>
                  : <><Calendar size={15} strokeWidth={1.8} /> Generate Schedule</>}
              </button>
            </div>
          </div>

          {/* Report result */}
          {report && (
            <div className="card" style={{ padding: 28, marginBottom: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <h3 style={{ fontSize: "1rem" }}>
                <BarChart2 size={16} strokeWidth={1.8} style={{ display: "inline", marginRight: 6 }} />
                Performance Report — <span style={{ color: "var(--accent)" }}>{student?.name}</span>
              </h3>
                <button className="btn btn-ghost btn-sm" onClick={handleReport} disabled={reportLoading}>
                <RotateCcw size={13} strokeWidth={2} /> Regenerate
              </button>
              </div>
              <ReportView data={report} />
            </div>
          )}

          {/* Schedule result */}
          {schedule && (
            <div className="card" style={{ padding: 28 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <h3 style={{ fontSize: "1rem" }}>
                <Calendar size={16} strokeWidth={1.8} style={{ display: "inline", marginRight: 6 }} />
                Study Schedule — <span style={{ color: "var(--success)" }}>{student?.name}</span>
              </h3>
                <button className="btn btn-ghost btn-sm"
                style={{ color: "var(--success)", borderColor: "var(--success-border)" }}
                onClick={handleSchedule} disabled={scheduleLoading}>
                <RotateCcw size={13} strokeWidth={2} /> Regenerate
              </button>
              </div>
              <ScheduleView data={schedule} />
            </div>
          )}

          {/* Empty state */}
          {!report && !schedule && !reportLoading && !scheduleLoading && (
            <div style={{ textAlign: "center", padding: "40px 20px", color: "var(--text-muted)" }}>
              <div style={{ display: "flex", justifyContent: "center", marginBottom: 12 }}>
                <Sparkles size={48} strokeWidth={1} style={{ color: "var(--accent)" }} />
              </div>
              <p>Click a button above to generate AI-powered insights for this student.</p>
            </div>
          )}
        </div>
      )}

      {/* ── CHAT TAB ──────────────────────────────────────────────────────── */}
      {tab === "chat" && (
        <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 320px)", minHeight: 500 }}>
          {/* Messages area */}
          <div style={{
            flex: 1, overflowY: "auto", padding: "20px 4px",
            display: "flex", flexDirection: "column",
          }}>
            {messages.length === 0 && (
              <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--text-muted)" }}>
              <div style={{ display: "flex", justifyContent: "center", marginBottom: 16 }}>
                <Bot size={52} strokeWidth={1} style={{ color: "var(--accent)" }} />
              </div>
                <h3 style={{ color: "var(--text-secondary)", marginBottom: 8 }}>
                  Chat about {student?.name}
                </h3>
                <p style={{ fontSize: "0.88rem", maxWidth: 420, margin: "0 auto 24px" }}>
                  I have access to all of {student?.name}'s academic data. Ask me anything about their performance, 
                  suggest improvements, or explore their counseling history.
                </p>
                {/* Starter prompts */}
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center" }}>
                  {[
                    "What are the weakest subjects?",
                    "How has attendance affected performance?",
                    "What study tips would help most?",
                    "Summarize the counseling issues",
                    "Compare PT1 vs PT2 improvement",
                    "What grade is at risk of failing?",
                  ].map(q => (
                    <button key={q} className="btn btn-ghost btn-sm"
                      style={{ fontSize: "0.78rem", borderColor: "var(--accent-border)", color: "var(--text-secondary)" }}
                      onClick={() => { setInput(q); inputRef.current?.focus(); }}>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => <ChatBubble key={i} msg={msg} />)}

            {/* Typing indicator */}
            {chatLoading && (
              <div style={{ display: "flex", alignItems: "flex-start", marginBottom: 16 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: "50%", flexShrink: 0,
                  background: "var(--accent)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}><Bot size={18} color="#fff" strokeWidth={1.8} /></div>
                <div style={{
                  padding: "14px 18px", borderRadius: "4px 16px 16px 16px",
                  background: "var(--surface-muted)", border: "1px solid var(--glass-border)",
                  display: "flex", gap: 4, alignItems: "center", marginLeft: 10,
                }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{
                      width: 7, height: 7, borderRadius: "50%",
                      background: "var(--accent)",
                      animation: `bounce 1.2s ${i * 0.2}s infinite`,
                    }} />
                  ))}
                </div>
              </div>
            )}

            {chatError && (
              <div className="alert alert-error" style={{ marginBottom: 12, fontSize: "0.82rem" }}>
                {chatError}
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input bar */}
          <form onSubmit={handleSend} style={{
            display: "flex", gap: 10, padding: "16px 0 0",
            borderTop: "1px solid var(--glass-border)",
          }}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Ask about ${student?.name || "this student"}… (Enter to send, Shift+Enter for newline)`}
              rows={1}
              disabled={chatLoading}
              style={{
                flex: 1, background: "var(--glass-bg)", border: "1px solid var(--glass-border)",
                borderRadius: 12, color: "var(--text-primary)", padding: "12px 16px",
                fontSize: "0.88rem", resize: "none", outline: "none", lineHeight: 1.5,
                transition: "border-color 0.2s", fontFamily: "inherit",
              }}
              onFocus={e => e.target.style.borderColor = "var(--accent-border)"}
              onBlur={e => e.target.style.borderColor = "var(--glass-border)"}
            />
            <button type="submit" disabled={!input.trim() || chatLoading}
              className="btn btn-primary"
              style={{ alignSelf: "flex-end", minWidth: 56, height: 46 }}>
              {chatLoading ? <span className="spinner" /> : <Send size={16} strokeWidth={2} />}
            </button>
          </form>
        </div>
      )}

      <style>{`
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-6px); }
        }
      `}</style>
    </>
  );
}
