"use client"

import { useState, useEffect, useRef } from "react"
import { useAuth, useAuthenticatedFetch } from "../context/AuthContext"

type View = "inbox" | "settings"
type RunStatus = "idle" | "running" | "done" | "error"

interface LabelInfo {
  name: string
  gmail_label_id: string | null
}

interface EmailRecord {
  gmail_message_id: string
  subject: string
  confirmed_labels: { record_id: string; label_name: string }[]
  suggested_labels: { record_id: string; label_name: string }[]
  applied_at: string
}

export default function Dashboard() {
  const { user, isAuthenticated, loading, logout } = useAuth()
  const authFetch = useAuthenticatedFetch()

  const SERVER_URL = process.env.NEXT_PUBLIC_SERVER_URL

  const [userName, setUserName] = useState("Name")
  const [userEmail, setUserEmail] = useState("user@mail.com")

  const [activeView, setActiveView] = useState<View>("inbox")

  // User settings
  const [autoSync, setAutoSync] = useState(false)
  const [autoApply, setAutoApply] = useState(false)
  const [userLabels, setUserLabels] = useState<LabelInfo[]>([])

  // Email records
  const [recentEmails, setRecentEmails] = useState<EmailRecord[]>([])

  // Manual run
  const [runStatus, setRunStatus] = useState<RunStatus>("idle")
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Manual label picker — stores the gmail_message_id whose picker is open
  const [openLabelPicker, setOpenLabelPicker] = useState<string | null>(null)

  useEffect(() => {
    if (user) {
      setUserName(user.name)
      setUserEmail(user.email)
    }
  }, [user])

  // Fetch user doc: settings + labels
  useEffect(() => {
    if (!isAuthenticated || loading) return
    authFetch(`${SERVER_URL}/api/user`)
      .then((res) => res.json())
      .then((data) => {
        setAutoSync(data.auto_sync ?? false)
        setAutoApply(data.auto_apply ?? false)
        const labelsObj: Record<string, any> = data.labels ?? {}
        setUserLabels(
          Object.values(labelsObj).map((l) => ({
            name: l.name as string,
            gmail_label_id: (l.gmail_label_id as string | null) ?? null,
          }))
        )
      })
      .catch(() => {})
  }, [isAuthenticated, loading])

  // Fetch recent emails
  useEffect(() => {
    if (!isAuthenticated || loading) return
    authFetch(`${SERVER_URL}/api/label-records/recent`)
      .then((res) => res.json())
      .then((data) => setRecentEmails(data.emails ?? []))
      .catch(() => {})
  }, [isAuthenticated, loading])

  // Close label picker on outside click
  useEffect(() => {
    if (!openLabelPicker) return
    const handler = () => setOpenLabelPicker(null)
    window.addEventListener("click", handler)
    return () => window.removeEventListener("click", handler)
  }, [openLabelPicker])

  // Cleanup poll interval on unmount
  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  // ── Manual run ─────────────────────────────────────────────────────────────

  const handleRunNow = async () => {
    if (runStatus === "running") return
    setRunStatus("running")
    try {
      const res = await authFetch(`${SERVER_URL}/api/gmail/messages?triggered_by=manual`)
      const { task_id } = await res.json()
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await authFetch(`${SERVER_URL}/api/gmail/status/${task_id}`)
          const { status } = await statusRes.json()
          if (status === "done") {
            clearInterval(pollRef.current!)
            setRunStatus("done")
            authFetch(`${SERVER_URL}/api/label-records/recent`)
              .then((r) => r.json())
              .then((data) => setRecentEmails(data.emails ?? []))
              .catch(() => {})
            setTimeout(() => setRunStatus("idle"), 3000)
          } else if (status === "failed") {
            clearInterval(pollRef.current!)
            setRunStatus("error")
            setTimeout(() => setRunStatus("idle"), 4000)
          }
        } catch {
          clearInterval(pollRef.current!)
          setRunStatus("error")
          setTimeout(() => setRunStatus("idle"), 4000)
        }
      }, 2000)
    } catch {
      setRunStatus("error")
      setTimeout(() => setRunStatus("idle"), 4000)
    }
  }

  // ── Settings toggles ───────────────────────────────────────────────────────

  const handleToggleAutoSync = async () => {
    const next = !autoSync
    setAutoSync(next)
    authFetch(`${SERVER_URL}/api/user`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ auto_sync: next }),
    }).catch(() => setAutoSync(!next))
  }

  const handleToggleAutoApply = async () => {
    const next = !autoApply
    setAutoApply(next)
    authFetch(`${SERVER_URL}/api/user`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ auto_apply: next }),
    }).catch(() => setAutoApply(!next))
  }

  // ── Label record actions ───────────────────────────────────────────────────

  const handleUndo = async (recordId: string, msgId: string) => {
    await authFetch(`${SERVER_URL}/api/label-records/${recordId}/undo`, { method: "POST" })
    setRecentEmails((prev) =>
      prev
        .map((e) =>
          e.gmail_message_id === msgId
            ? { ...e, confirmed_labels: e.confirmed_labels.filter((l) => l.record_id !== recordId) }
            : e
        )
        .filter((e) => e.confirmed_labels.length > 0 || e.suggested_labels.length > 0)
    )
  }

  const handleConfirm = async (recordId: string, msgId: string) => {
    await authFetch(`${SERVER_URL}/api/label-records/${recordId}/confirm`, { method: "POST" })
    setRecentEmails((prev) =>
      prev.map((e) => {
        if (e.gmail_message_id !== msgId) return e
        const confirmed = e.suggested_labels.find((l) => l.record_id === recordId)
        return {
          ...e,
          suggested_labels: e.suggested_labels.filter((l) => l.record_id !== recordId),
          confirmed_labels: confirmed ? [...e.confirmed_labels, confirmed] : e.confirmed_labels,
        }
      })
    )
  }

  const handleReject = async (recordId: string, msgId: string) => {
    await authFetch(`${SERVER_URL}/api/label-records/${recordId}/reject`, { method: "POST" })
    setRecentEmails((prev) =>
      prev
        .map((e) =>
          e.gmail_message_id === msgId
            ? { ...e, suggested_labels: e.suggested_labels.filter((l) => l.record_id !== recordId) }
            : e
        )
        .filter((e) => e.confirmed_labels.length > 0 || e.suggested_labels.length > 0)
    )
  }

  const handleManualLabel = async (msgId: string, subject: string, label: LabelInfo) => {
    setOpenLabelPicker(null)
    const res = await authFetch(`${SERVER_URL}/api/label-records/manual`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gmail_message_id: msgId, label_name: label.name }),
    })
    if (!res.ok) return
    const { record } = await res.json()
    setRecentEmails((prev) => {
      const existing = prev.find((e) => e.gmail_message_id === msgId)
      if (existing) {
        return prev.map((e) =>
          e.gmail_message_id === msgId
            ? {
                ...e,
                confirmed_labels: [
                  ...e.confirmed_labels,
                  { record_id: record.record_id, label_name: label.name },
                ],
              }
            : e
        )
      }
      return [
        {
          gmail_message_id: msgId,
          subject,
          confirmed_labels: [{ record_id: record.record_id, label_name: label.name }],
          suggested_labels: [],
          applied_at: new Date().toISOString(),
        },
        ...prev,
      ]
    })
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  const appliedLabelNames = (email: EmailRecord): Set<string> => {
    const s = new Set<string>()
    email.confirmed_labels.forEach((l) => s.add(l.label_name))
    email.suggested_labels.forEach((l) => s.add(l.label_name))
    return s
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen flex overflow-hidden bg-gray-50 text-slate-900" style={{ fontFamily: "'Manrope', sans-serif" }}>

      {/* Sidebar */}
      <aside className="hidden md:flex flex-col h-screen w-64 sticky left-0 top-0 bg-slate-100 py-8 px-4 space-y-6 flex-shrink-0">
        <div className="px-2 mb-4">
          <span className="text-xl font-black text-red-700 tracking-tighter">Labl</span>
          <div className="mt-4">
            <p className="text-sm font-semibold tracking-wide uppercase text-red-700">Inbox</p>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">AI Labeling Active</p>
          </div>
        </div>

        <nav className="flex-grow space-y-1">
          <button
            onClick={() => setActiveView("inbox")}
            className={`w-full flex items-center gap-3 px-3 py-2 font-bold transition-all active:translate-x-1 duration-200 ${activeView === "inbox" ? "text-red-700" : "text-slate-500 hover:text-red-600"}`}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 22 }}>inbox</span>
            <span className="text-sm font-semibold tracking-wide uppercase">Inbox</span>
          </button>
          <a className="flex items-center gap-3 px-3 py-2 text-slate-500 hover:text-red-600 transition-all active:translate-x-1 duration-200" href="#">
            <span className="material-symbols-outlined" style={{ fontSize: 22 }}>label</span>
            <span className="text-sm font-semibold tracking-wide uppercase">Labels</span>
          </a>
          <a className="flex items-center gap-3 px-3 py-2 text-slate-500 hover:text-red-600 transition-all active:translate-x-1 duration-200" href="#">
            <span className="material-symbols-outlined" style={{ fontSize: 22 }}>history</span>
            <span className="text-sm font-semibold tracking-wide uppercase">Activity</span>
          </a>
        </nav>

        <div className="pt-6 mt-6 border-t border-slate-200 space-y-1">
          <button
            onClick={() => setActiveView("settings")}
            className={`w-full flex items-center gap-3 px-3 py-2 transition-all ${activeView === "settings" ? "text-red-700 font-bold" : "text-slate-500 hover:text-red-600"}`}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 22 }}>settings</span>
            <span className="text-sm font-semibold tracking-wide uppercase">Settings</span>
          </button>
          <a className="flex items-center gap-3 px-3 py-2 text-slate-500 hover:text-red-600 transition-all" href="#">
            <span className="material-symbols-outlined" style={{ fontSize: 22 }}>help</span>
            <span className="text-sm font-semibold tracking-wide uppercase">Support</span>
          </a>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex-grow flex flex-col min-w-0 bg-gray-50">

        {/* Top bar */}
        <header className="w-full sticky top-0 bg-slate-50 flex justify-between items-center px-6 py-4 z-10 border-b border-slate-200">
          <div className="flex items-center gap-4">
            <div className="h-8 w-8 rounded-full bg-red-100 flex items-center justify-center text-red-700 font-bold text-sm shrink-0">
              {userName.charAt(0).toUpperCase()}
            </div>
            <span className="text-sm font-medium text-slate-600">{userEmail}</span>
          </div>
          <div className="flex items-center gap-3">
            {/* Run Now */}
            <button
              onClick={handleRunNow}
              disabled={runStatus === "running"}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-150 active:scale-95 ${
                runStatus === "running"
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                  : runStatus === "done"
                  ? "bg-green-50 text-green-700 border border-green-200"
                  : runStatus === "error"
                  ? "bg-red-50 text-red-700 border border-red-200"
                  : "bg-red-700 text-white hover:bg-red-800"
              }`}
            >
              {runStatus === "running" ? (
                <>
                  <span className="material-symbols-outlined animate-spin" style={{ fontSize: 16 }}>refresh</span>
                  Running…
                </>
              ) : runStatus === "done" ? (
                <>
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>check_circle</span>
                  Done
                </>
              ) : runStatus === "error" ? (
                <>
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>error</span>
                  Failed
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>play_arrow</span>
                  Run Now
                </>
              )}
            </button>
            <button
              onClick={() => logout()}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-slate-200 active:scale-95 duration-150 text-red-700"
            >
              Sign Out
            </button>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-grow overflow-y-auto p-6 md:p-10">
          <div className="max-w-6xl mx-auto space-y-12">

            {activeView === "inbox" ? (
              <>
                <section className="space-y-2">
                  <h1 className="text-5xl font-extrabold tracking-tighter text-slate-900">Inbox</h1>
                  <p className="text-slate-500 font-medium">Archiving privacy via AI-driven categorization.</p>
                </section>

                <div className="space-y-3">
                  {recentEmails.length === 0 ? (
                    <div className="bg-slate-50 rounded-xl p-10 flex flex-col items-center justify-center gap-3 border border-slate-200">
                      <span className="material-symbols-outlined text-slate-300" style={{ fontSize: 48 }}>mark_email_read</span>
                      <p className="text-slate-400 font-semibold text-sm">No new messages to show.</p>
                    </div>
                  ) : (
                    recentEmails.map((email) => {
                      const applied = appliedLabelNames(email)
                      const availableLabels = userLabels.filter((l) => !applied.has(l.name))
                      return (
                        <div
                          key={email.gmail_message_id}
                          className="group bg-slate-50 hover:bg-slate-200 transition-all duration-300 rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4"
                        >
                          <div className="flex flex-col gap-1 min-w-0">
                            <a
                              href={`https://mail.google.com/mail/u/0/#all/${email.gmail_message_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="font-bold text-slate-900 truncate hover:text-red-700 transition-colors cursor-pointer"
                            >
                              {email.subject}
                            </a>
                          </div>

                          <div className="flex items-center flex-wrap gap-2 shrink-0">
                            {email.confirmed_labels.map((lbl) => (
                              <div key={lbl.record_id} className="flex items-center gap-1.5 bg-red-700 text-white px-3 py-1.5 rounded-xl text-xs font-bold">
                                {lbl.label_name}
                                <button
                                  className="ml-2 opacity-60 hover:opacity-100 transition-opacity"
                                  title="Undo"
                                  onClick={() => handleUndo(lbl.record_id, email.gmail_message_id)}
                                >
                                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>u_turn_left</span>
                                </button>
                              </div>
                            ))}
                            {email.suggested_labels.map((lbl) => (
                              <div key={lbl.record_id} className="flex items-center gap-1.5 bg-amber-50 text-amber-800 px-3 py-1.5 rounded-full text-xs font-bold ring-1 ring-amber-200">
                                <span className="material-symbols-outlined" style={{ fontSize: 14, fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
                                {lbl.label_name}
                                <div className="flex items-center ml-2 border-l border-amber-300 pl-2 gap-2">
                                  <button
                                    className="hover:text-green-600 transition-colors"
                                    title="Confirm"
                                    onClick={() => handleConfirm(lbl.record_id, email.gmail_message_id)}
                                  >
                                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>check</span>
                                  </button>
                                  <button
                                    className="hover:text-red-600 transition-colors"
                                    title="Reject"
                                    onClick={() => handleReject(lbl.record_id, email.gmail_message_id)}
                                  >
                                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>close</span>
                                  </button>
                                </div>
                              </div>
                            ))}

                            {/* Manual label picker */}
                            {availableLabels.length > 0 && (
                              <div className="relative">
                                <button
                                  title="Add label"
                                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-bold text-slate-500 hover:text-red-700 hover:bg-red-50 transition-colors border border-slate-200 hover:border-red-200"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    setOpenLabelPicker(
                                      openLabelPicker === email.gmail_message_id ? null : email.gmail_message_id
                                    )
                                  }}
                                >
                                  <span className="material-symbols-outlined" style={{ fontSize: 14 }}>add</span>
                                  Label
                                </button>
                                {openLabelPicker === email.gmail_message_id && (
                                  <div
                                    className="absolute right-0 top-full mt-1 z-20 bg-white rounded-xl shadow-xl border border-slate-200 py-1 min-w-[140px]"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    {availableLabels.map((lbl) => (
                                      <button
                                        key={lbl.name}
                                        className="w-full text-left px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-red-50 hover:text-red-700 transition-colors"
                                        onClick={() => handleManualLabel(email.gmail_message_id, email.subject, lbl)}
                                      >
                                        {lbl.name}
                                      </button>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-12">
                  <div className="bg-slate-50 border border-slate-200 p-6 rounded-xl space-y-2">
                    <p className="text-[10px] font-black tracking-widest text-slate-500 uppercase">Label Accuracy</p>
                    <p className="text-3xl font-extrabold text-red-700">—</p>
                    <p className="text-xs text-slate-400">Based on your confirmed labels.</p>
                  </div>
                  <div className="bg-slate-50 border border-slate-200 p-6 rounded-xl space-y-2">
                    <p className="text-[10px] font-black tracking-widest text-slate-500 uppercase">Labels Active</p>
                    <p className="text-3xl font-extrabold text-slate-900">{userLabels.length}</p>
                    <p className="text-xs text-slate-400">Custom labels configured for your inbox.</p>
                  </div>
                  <div className="bg-slate-50 border border-slate-200 p-6 rounded-xl space-y-2 border-l-4 border-l-red-700">
                    <p className="text-[10px] font-black tracking-widest text-red-700 uppercase">System Status</p>
                    <p className="text-3xl font-extrabold text-slate-900">Operational</p>
                    <p className="text-xs text-slate-400">AI labeling pipeline is running.</p>
                  </div>
                </div>
              </>
            ) : (
              /* Settings */
              <>
                <section className="space-y-2">
                  <h1 className="text-5xl font-extrabold tracking-tighter text-slate-900">Settings</h1>
                  <p className="text-slate-500 font-medium">Manage how Labl processes your inbox.</p>
                </section>

                <div className="space-y-4 max-w-xl">
                  <div className="bg-white border border-slate-200 rounded-xl p-5 flex items-center justify-between gap-4">
                    <div>
                      <p className="font-bold text-slate-900 text-sm">Automatic Sync</p>
                      <p className="text-xs text-slate-500 mt-0.5">Automatically run the labeling pipeline on a schedule.</p>
                    </div>
                    <button
                      role="switch"
                      aria-checked={autoSync}
                      onClick={handleToggleAutoSync}
                      className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors duration-200 focus:outline-none ${autoSync ? "bg-red-700" : "bg-slate-200"}`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform duration-200 ${autoSync ? "translate-x-6" : "translate-x-1"}`} />
                    </button>
                  </div>

                  <div className="bg-white border border-slate-200 rounded-xl p-5 flex items-center justify-between gap-4">
                    <div>
                      <p className="font-bold text-slate-900 text-sm">Auto-Apply Labels</p>
                      <p className="text-xs text-slate-500 mt-0.5">Apply high-confidence labels directly instead of suggesting them for review.</p>
                    </div>
                    <button
                      role="switch"
                      aria-checked={autoApply}
                      onClick={handleToggleAutoApply}
                      className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors duration-200 focus:outline-none ${autoApply ? "bg-red-700" : "bg-slate-200"}`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform duration-200 ${autoApply ? "translate-x-6" : "translate-x-1"}`} />
                    </button>
                  </div>
                </div>
              </>
            )}

          </div>
        </main>
      </div>

      {/* FAB */}
      <button className="fixed bottom-8 right-8 h-16 w-16 rounded-full bg-red-700 text-white flex items-center justify-center shadow-2xl transition-transform hover:scale-105 active:scale-95 duration-150 group">
        <span className="material-symbols-outlined" style={{ fontSize: 28 }}>edit</span>
        <span className="absolute right-full mr-4 bg-slate-900 text-white text-xs font-bold px-3 py-1.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          Create Label
        </span>
      </button>

    </div>
  )
}
