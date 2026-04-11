"use client"

import { useState, useEffect } from "react"
import { useAuth, useAuthenticatedFetch } from "../context/AuthContext"

export default function Dashboard() {
  const {user, isAuthenticated, loading} = useAuth();
  const authFetch = useAuthenticatedFetch();
  const [userName, setUserName] = useState("Name")
  const [userEmail, setUserEmail] = useState("user@mail.com")

  const SERVER_URL = process.env.NEXT_PUBLIC_SERVER_URL

  const [labels, setLabels] = useState<string[]>([])
  const [newLabel, setNewLabel] = useState("")
  const [recentEmails] = useState<{
    id: number
    sender: string
    subject: string
    confirmedLabel?: string
    suggestedLabel?: string
    encrypted?: boolean
    priority?: boolean
  }[]>([])

  useEffect(() => {
    if (!isAuthenticated && !loading) {
      console.log("Not authenticated")
    } else {
      if (user) {
        setUserName(user.name)
        setUserEmail(user.email)
      }
    }
  }, [loading, isAuthenticated])

  const handleAddLabel = async () => {
    const res = await authFetch(`${SERVER_URL}/api/gmail/labels`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newLabel }),
    })
  }

  const addLabel = () => {
    if (newLabel.trim() && !labels.includes(newLabel.trim())) {
      setLabels([...labels, newLabel.trim()])
      handleAddLabel()
      setNewLabel("")
    }
  }

  const removeLabel = (label: string) => {
    setLabels(labels.filter((l) => l !== label))
  }

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
          <a
            className="flex items-center gap-3 px-3 py-2 text-red-700 font-bold hover:text-red-600 transition-all active:translate-x-1 duration-200"
            href="#"
          >
            <span className="material-symbols-outlined" style={{ fontSize: 22 }}>inbox</span>
            <span className="text-sm font-semibold tracking-wide uppercase">Inbox</span>
          </a>
          <a
            className="flex items-center gap-3 px-3 py-2 text-slate-500 hover:text-red-600 transition-all active:translate-x-1 duration-200"
            href="#"
          >
            <span className="material-symbols-outlined" style={{ fontSize: 22 }}>label</span>
            <span className="text-sm font-semibold tracking-wide uppercase">Labels</span>
          </a>
          <a
            className="flex items-center gap-3 px-3 py-2 text-slate-500 hover:text-red-600 transition-all active:translate-x-1 duration-200"
            href="#"
          >
            <span className="material-symbols-outlined" style={{ fontSize: 22 }}>history</span>
            <span className="text-sm font-semibold tracking-wide uppercase">Activity</span>
          </a>
          <a
            className="flex items-center gap-3 px-3 py-2 text-slate-500 hover:text-red-600 transition-all active:translate-x-1 duration-200"
            href="#"
          >
            <span className="material-symbols-outlined" style={{ fontSize: 22 }}>analytics</span>
            <span className="text-sm font-semibold tracking-wide uppercase">Insights</span>
          </a>
        </nav>

        <div className="pt-6 mt-6 border-t border-slate-200 space-y-1">
          <a
            className="flex items-center gap-3 px-3 py-2 text-slate-500 hover:text-red-600 transition-all"
            href="#"
          >
            <span className="material-symbols-outlined" style={{ fontSize: 22 }}>settings</span>
            <span className="text-sm font-semibold tracking-wide uppercase">Settings</span>
          </a>
          <a
            className="flex items-center gap-3 px-3 py-2 text-slate-500 hover:text-red-600 transition-all"
            href="#"
          >
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
          <button className="px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-slate-200 active:scale-95 duration-150 text-red-700">
            Sign Out
          </button>
        </header>

        {/* Main content */}
        <main className="flex-grow overflow-y-auto p-6 md:p-10">
          <div className="max-w-6xl mx-auto space-y-12">

            {/* Editorial header */}
            <section className="space-y-2">
              <h1 className="text-5xl font-extrabold tracking-tighter text-slate-900">Inbox</h1>
              <p className="text-slate-500 font-medium">Archiving privacy via AI-driven categorization.</p>
            </section>

            {/* Email list */}
            <div className="space-y-3">
              {recentEmails.length === 0 ? (
                <div className="bg-slate-50 rounded-xl p-10 flex flex-col items-center justify-center gap-3 border border-slate-200">
                  <span className="material-symbols-outlined text-slate-300" style={{ fontSize: 48 }}>mark_email_read</span>
                  <p className="text-slate-400 font-semibold text-sm">No new messages to show.</p>
                </div>
              ) : (
                recentEmails.map((email) => (
                  <div
                    key={email.id}
                    className="group bg-slate-50 hover:bg-slate-200 transition-all duration-300 rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="flex flex-col gap-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <span className="font-bold text-slate-900 truncate">{email.sender}</span>
                        {email.encrypted && (
                          <span className="text-[10px] bg-slate-200 px-1.5 py-0.5 rounded font-black tracking-widest text-slate-600 uppercase">Encrypted</span>
                        )}
                        {email.priority && (
                          <span className="text-[10px] bg-red-600 text-white px-1.5 py-0.5 rounded font-black tracking-widest uppercase">Priority</span>
                        )}
                      </div>
                      <h3 className="text-sm text-slate-500 font-medium truncate">{email.subject}</h3>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      {email.confirmedLabel && (
                        <div className="flex items-center gap-1.5 bg-red-700 text-white px-3 py-1.5 rounded-xl text-xs font-bold">
                          {email.confirmedLabel}
                          <button className="ml-2 opacity-60 hover:opacity-100 transition-opacity" title="Undo">
                            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>u_turn_left</span>
                          </button>
                        </div>
                      )}
                      {email.suggestedLabel && (
                        <div className="flex items-center gap-1.5 bg-amber-50 text-amber-800 px-3 py-1.5 rounded-full text-xs font-bold ring-1 ring-amber-200">
                          <span className="material-symbols-outlined" style={{ fontSize: 14, fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
                          {email.suggestedLabel}
                          <div className="flex items-center ml-2 border-l border-amber-300 pl-2 gap-2">
                            <button className="hover:text-green-600 transition-colors" title="Confirm">
                              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>check</span>
                            </button>
                            <button className="hover:text-red-600 transition-colors" title="Reject">
                              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>close</span>
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Metrics footer */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-12">
              <div className="bg-slate-50 border border-slate-200 p-6 rounded-xl space-y-2">
                <p className="text-[10px] font-black tracking-widest text-slate-500 uppercase">Label Accuracy</p>
                <p className="text-3xl font-extrabold text-red-700">—</p>
                <p className="text-xs text-slate-400">Based on your confirmed labels.</p>
              </div>
              <div className="bg-slate-50 border border-slate-200 p-6 rounded-xl space-y-2">
                <p className="text-[10px] font-black tracking-widest text-slate-500 uppercase">Labels Active</p>
                <p className="text-3xl font-extrabold text-slate-900">{labels.length}</p>
                <p className="text-xs text-slate-400">Custom labels configured for your inbox.</p>
              </div>
              <div className="bg-slate-50 border border-slate-200 p-6 rounded-xl space-y-2 border-l-4 border-l-red-700">
                <p className="text-[10px] font-black tracking-widest text-red-700 uppercase">System Status</p>
                <p className="text-3xl font-extrabold text-slate-900">Operational</p>
                <p className="text-xs text-slate-400">AI labeling pipeline is running.</p>
              </div>
            </div>

          </div>
        </main>
      </div>

      {/* FAB */}
      <button className="fixed bottom-8 right-8 h-16 w-16 rounded-full bg-red-700 text-white flex items-center justify-center shadow-2xl transition-transform hover:scale-105 active:scale-95 duration-150 group">
        <span className="material-symbols-outlined" style={{ fontSize: 28 }}>edit</span>
        <span className="absolute right-full mr-4 bg-slate-900 text-white text-xs font-bold px-3 py-1.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          Compose
        </span>
      </button>

    </div>
  )
}
