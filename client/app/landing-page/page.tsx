'use client'
import Link from "next/link"
import { useAuth } from "../context/AuthContext"

export default function Home() {
  const { login } = useAuth();

  const handleLogin = () => {
    login();
  }

  return (
    <div className="min-h-screen bg-[#f8f9fa] text-[#191c1d]" style={{ fontFamily: "'Manrope', sans-serif" }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&display=swap');`}</style>

      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100">
        <div className="flex justify-between items-center max-w-7xl mx-auto px-6 h-16">
          <div className="text-3xl font-black tracking-tighter text-red-700">Labl</div>
          <div className="hidden md:flex items-center space-x-12">
            <a className="text-slate-600 font-medium hover:text-red-600 transition-colors text-sm tracking-tight" href="#how-it-works">Overview</a>
            <a className="text-slate-600 font-medium hover:text-red-600 transition-colors text-sm tracking-tight" href="#security">Security</a>
            <a className="text-slate-600 font-medium hover:text-red-600 transition-colors text-sm tracking-tight" href="#accuracy">Accuracy</a>
          </div>
          <div className="flex items-center space-x-6">
            <button
              onClick={handleLogin}
              className="text-slate-600 font-medium hover:text-red-600 transition-colors text-sm tracking-tight"
            >
              Log In
            </button>
            <button
              onClick={handleLogin}
              className="bg-[#b5110e] text-white px-5 py-2 rounded-xl font-medium hover:bg-[#d93025] transition-all active:scale-95 duration-100 text-sm"
            >
              Get Started
            </button>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-20">
        {/* Hero Section */}
        <section className="max-w-7xl mx-auto px-6 mb-32">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
            <div className="lg:col-span-7 space-y-10">
              <div className="space-y-4">
                <span className="inline-block py-1 px-3 rounded-full bg-[#ffdad5] text-[#410001] text-xs font-bold tracking-widest uppercase">
                  Privacy & Security First
                </span>
                <h1 className="text-5xl md:text-7xl font-extrabold tracking-tighter leading-[0.95] text-[#191c1d]">
                  Security-First <br />
                  <span className="text-[#b5110e]">Intelligence</span> <br />
                  for your Inbox.
                </h1>
              </div>
              <p className="text-xl md:text-2xl text-slate-500 font-light leading-relaxed max-w-2xl">
                Labl embeds and categorizes your mail locally on our servers. Your sensitive data never leaks to external Large Language Models or centralized cloud training sets.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 pt-4">
                <button
                  onClick={handleLogin}
                  className="flex items-center justify-center gap-3 bg-white text-[#191c1d] px-8 py-4 rounded-xl border border-slate-200 hover:border-[#b5110e] transition-all shadow-sm font-bold tracking-tight"
                >
                  {/* Google Logo SVG */}
                  <svg className="w-5 h-5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                  </svg>
                  <span>Continue with Google</span>
                </button>
                {/*
                <div className="flex items-center px-4">
                  <div className="flex -space-x-2">
                    <div className="w-8 h-8 rounded-full border-2 border-[#f8f9fa] bg-[#edeeef]"></div>
                    <div className="w-8 h-8 rounded-full border-2 border-[#f8f9fa] bg-[#e7e8e9]"></div>
                    <div className="w-8 h-8 rounded-full border-2 border-[#f8f9fa] bg-[#d9dadb]"></div>
                  </div>
                  <span className="ml-4 text-sm font-medium text-slate-500">Used by 2,000+ security experts</span>
                </div>
                */}
              </div>
            </div>

            <div className="lg:col-span-5 relative">
              <div className="aspect-square bg-[#f3f4f5] rounded-3xl overflow-hidden relative group">
                <div className="absolute inset-0 bg-gradient-to-br from-[#b5110e]/5 to-transparent"></div>
                <div className="absolute inset-0 flex items-center justify-center p-12">
                  <div className="grid grid-cols-3 gap-8">
                    <div className="w-24 h-24 bg-white rounded-2xl flex items-center justify-center shadow-lg transform -rotate-6 transition-transform group-hover:rotate-0">
                      <svg className="w-10 h-10 text-[#b5110e]" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>
                      </svg>
                    </div>
                    <div className="w-24 h-24 bg-[#b5110e] rounded-2xl flex items-center justify-center shadow-xl transform translate-y-8">
                      <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
                      </svg>
                    </div>
                    <div className="w-24 h-24 bg-white rounded-2xl flex items-center justify-center shadow-lg transform rotate-12 transition-transform group-hover:rotate-0">
                      <svg className="w-10 h-10 text-[#b5110e]" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12.65 10C11.83 7.67 9.61 6 7 6c-3.31 0-6 2.69-6 6s2.69 6 6 6c2.61 0 4.83-1.67 5.65-4H17v4h4v-4h2v-4H12.65zM7 14c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

          {/* Inbox Mockup Section */}
        <section className="max-w-4xl mx-auto px-6 mb-32 -mt-16">
          <div className="rounded-2xl overflow-hidden shadow-2xl shadow-slate-300/60 border border-slate-200">
            {/* Window chrome */}
            <div className="bg-[#f0f1f3] border-b border-slate-200 px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-400"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                  <div className="w-3 h-3 rounded-full bg-green-400"></div>
                </div>
                <span className="text-sm font-medium text-slate-500 tracking-tight">inbox — labl</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-[#b5110e]/70"></div>
                <span className="text-xs text-[#b5110e]/70 font-medium tracking-wide">classifying...</span>
              </div>
            </div>
            {/* Email rows */}
            <div className="bg-white divide-y divide-slate-100">
              {[
                { initial: "J", name: "John Doe", subject: "Q2 roadmap review — action items", label: "WORK", color: "border-blue-500 text-blue-600" },
                { initial: "B", name: "ByteByteGo", subject: "The 5 things you need to know today", label: "NEWSLETTER", color: "border-amber-500 text-amber-600" },
                { initial: "C", name: "Chase Bank", subject: "Your statement is ready", label: "FINANCE", color: "border-emerald-500 text-emerald-600" },
                { initial: "A", name: "Amazon", subject: "Your order has shipped 📦", label: "RECEIPTS", color: "border-teal-500 text-teal-600" },
                { initial: "J", name: "Jane Doe", subject: "Weekend plans?", label: "PERSONAL", color: "border-violet-500 text-violet-600" },
                { initial: "P", name: "ProductHunt", subject: "🔥 Today's top products", label: "PROMOTIONS", color: "border-orange-500 text-orange-600" },
              ].map((row, i) => (
                <div key={i} className="flex items-center gap-4 px-6 py-4 hover:bg-slate-50 transition-colors">
                  <div className="w-9 h-9 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-bold text-slate-600">{row.initial}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-[#191c1d] truncate">{row.name}</p>
                    <p className="text-sm text-slate-400 truncate">{row.subject}</p>
                  </div>
                  <span className={`flex-shrink-0 text-[10px] font-bold tracking-widest border rounded px-2.5 py-1 ${row.color}`}>
                    {row.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

          {/* How It Works Section */}
        <section id="how-it-works" className="max-w-7xl mx-auto px-6 py-32">
          <div className="text-center mb-20">
            <span className="inline-block py-1 px-3 rounded-full bg-[#ffdad5] text-[#410001] text-xs font-bold tracking-widest uppercase mb-4">
              Transparent by default
            </span>
            <h2 className="text-5xl md:text-6xl font-black tracking-tighter text-[#191c1d]">How It Works</h2>
            <p className="mt-4 text-lg text-slate-500 max-w-xl mx-auto">
              Three steps. No black boxes. You can see exactly where your data goes — and where it doesn&apos;t.
            </p>
          </div>

          <div className="relative">
            {/* Connector line (desktop) */}
            <div className="hidden lg:block absolute top-10 left-[calc(16.67%+1rem)] right-[calc(16.67%+1rem)] h-px bg-slate-200 z-0"></div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 relative z-10">
              {/* Step 1 */}
              <div className="flex flex-col items-center text-center gap-6">
                <div className="w-20 h-20 rounded-2xl bg-white border border-slate-200 shadow-md flex items-center justify-center relative">
                  <span className="absolute -top-2.5 -right-2.5 w-6 h-6 rounded-full bg-[#b5110e] text-white text-xs font-bold flex items-center justify-center">1</span>
                  <svg className="w-9 h-9 text-[#b5110e]" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                  </svg>
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-bold tracking-tight text-[#191c1d]">Connect Gmail</h3>
                  <p className="text-slate-500 leading-relaxed text-sm max-w-xs mx-auto">
                    Authorize Labl via Google OAuth. We request read-write access — we never irreparably modify your inbox.
                  </p>
                </div>
                <div className="w-full bg-[#f3f4f5] rounded-xl p-4 text-left space-y-1.5">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <svg className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                    Read-only OAuth scope
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <svg className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                    Revoke access any time
                  </div>
                  <div className="flex items-center gap-2 text-xs text-red-400">
                    <svg className="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                    No permanent delete permissions (30-day window)
                  </div>
                </div>
              </div>

              {/* Step 2 */}
              <div className="flex flex-col items-center text-center gap-6">
                <div className="w-20 h-20 rounded-2xl bg-[#b5110e] shadow-lg shadow-[#b5110e]/30 flex items-center justify-center relative">
                  <span className="absolute -top-2.5 -right-2.5 w-6 h-6 rounded-full bg-[#191c1d] text-white text-xs font-bold flex items-center justify-center">2</span>
                  <svg className="w-9 h-9 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"/>
                  </svg>
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-bold tracking-tight text-[#191c1d]">Model Classifies</h3>
                  <p className="text-slate-500 leading-relaxed text-sm max-w-xs mx-auto">
                    Email subject lines and sender metadata are passed to our lightweight ML model. Their embeddings, run through a medoid-based semantic search algorithm.
                  </p>
                </div>
                <div className="w-full bg-[#f3f4f5] rounded-xl p-4 text-left space-y-1.5">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <svg className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                    Not-in-memory email content handling
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <svg className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                    No OpenAI / Anthropic API calls
                  </div>
                  <div className="flex items-center gap-2 text-xs text-red-400">
                    <svg className="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                    Email body never accessed
                  </div>
                </div>
              </div>

              {/* Step 3 */}
              <div className="flex flex-col items-center text-center gap-6">
                <div className="w-20 h-20 rounded-2xl bg-white border border-slate-200 shadow-md flex items-center justify-center relative">
                  <span className="absolute -top-2.5 -right-2.5 w-6 h-6 rounded-full bg-[#b5110e] text-white text-xs font-bold flex items-center justify-center">3</span>
                  <svg className="w-9 h-9 text-[#b5110e]" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M17.63 5.84C17.27 5.33 16.67 5 16 5L5 5.01C3.9 5.01 3 5.9 3 7v10c0 1.1.9 1.99 2 1.99L16 19c.67 0 1.27-.33 1.63-.84L22 12l-4.37-6.16z"/>
                  </svg>
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-bold tracking-tight text-[#191c1d]">Labels Applied</h3>
                  <p className="text-slate-500 leading-relaxed text-sm max-w-xs mx-auto">
                    Labels are written back to Gmail via the API. The classification result is stored; the email content never touches our database.
                  </p>
                </div>
                <div className="w-full bg-[#f3f4f5] rounded-xl p-4 text-left space-y-1.5">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <svg className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                    Label synced to Gmail instantly
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <svg className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                    Only label metadata and vector embeddings stored
                  </div>
                  <div className="flex items-center gap-2 text-xs text-red-400">
                    <svg className="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                    Email content never stored
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Private by Design Section */}
        <section id="security" className="bg-[#f3f4f5] py-32 overflow-hidden">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
              <div className="lg:col-span-4 space-y-8">
                <h2 className="text-5xl font-black tracking-tighter text-[#191c1d] leading-tight">
                  Private <br />
                  <span className="text-[#b5110e]">by Design</span>
                </h2>
                <p className="text-lg text-slate-500 font-medium leading-relaxed">
                  Most AI tools ingest your history to train their models. Labl flips the script.
                </p>
              </div>
              <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-px bg-slate-200/40">
                <div className="bg-[#f3f4f5] p-10 space-y-6">
                  <svg className="w-8 h-8 text-[#b5110e]" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M15 9H9v6h6V9zm-2 4h-2v-2h2v2zm8-2V9h-2V7c0-1.1-.9-2-2-2h-2V3h-2v2h-2V3H9v2H7c-1.1 0-2 .9-2 2v2H3v2h2v2H3v2h2v2c0 1.1.9 2 2 2h2v2h2v-2h2v2h2v-2h2c1.1 0 2-.9 2-2v-2h2v-2h-2v-2h2zm-4 6H7V7h10v10z"/>
                  </svg>
                  <h3 className="text-2xl font-bold tracking-tight">Local Execution</h3>
                  <p className="text-slate-500 leading-relaxed">
                    Our LLM architecture is optimized to run locally on our servers. The embedding process happens in our environment, and your sensitive content is never stored.
                  </p>
                </div>
                <div className="bg-[#f3f4f5] p-10 space-y-6">
                  <svg className="w-8 h-8 text-[#b5110e]" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  </svg>
                  <h3 className="text-2xl font-bold tracking-tight">Zero-Knowledge Storage</h3>
                  <p className="text-slate-500 leading-relaxed">
                    We store minimal metadata. Only the vector embeddings are stored. The core content of your emails is never mirrored to our servers and database. What you read stays where it belongs.
                  </p>
                </div>
                
              </div>
            </div>
          </div>
        </section>

        {/* Accuracy Section */}
        <section className="max-w-5xl mx-auto px-6 py-32" id="accuracy">
          <div className="relative bg-white rounded-[2rem] p-12 md:p-24 shadow-2xl shadow-[#b5110e]/5 border border-slate-200/60 overflow-hidden">
            <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-[#b5110e]/5 to-transparent pointer-events-none"></div>
            <div className="relative z-10 space-y-12">
              <div className="max-w-xl">
                <label className="text-s font-bold tracking-[0.2em] uppercase text-[#b5110e] block mb-6">
                  The Core System
                </label>
                <h2 className="text-4xl md:text-5xl font-extrabold tracking-tighter leading-tight mb-8 text-[#191c1d]">
                  Smarter with every label.
                </h2>
                <div className="space-y-6 text-slate-500 text-lg">
                  <div className="flex items-start gap-4">
                    <svg className="w-6 h-6 text-[#b5110e] mt-1 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    <p>Bootstraps label patterns from just a few confirmed examples.</p>
                  </div>
                  <div className="flex items-start gap-4">
                    <svg className="w-6 h-6 text-[#b5110e] mt-1 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    <p>Labels refine automatically as you accept or reject suggestions and/or labels.</p>
                  </div>
                  <div className="flex items-start gap-4">
                    <svg className="w-6 h-6 text-[#b5110e] mt-1 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    <p>Graduates to full k-means clustering as your confirmed labels accumulate.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="max-w-7xl mx-auto px-6 py-32 text-center">
          <div className="max-w-3xl mx-auto space-y-10">
            <h2 className="text-5xl md:text-7xl font-black tracking-tighter text-[#191c1d]">
              Ready for a <br />
              <span className="text-[#b5110e]">neater, cleaner inbox?</span>
            </h2>
            <div>
              <p className="text-xl text-slate-500 font-medium leading-relaxed">
                Your inbox, but smarter and more organized. Get started with Labl today.
              </p>
              <p className="text-xl text-slate-500 font-medium leading-relaxed">
                For free, forever.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row justify-center gap-6">
              <button
                onClick={handleLogin}
                className="bg-[#b5110e] text-white px-8 py-4 rounded-xl font-bold text-lg hover:bg-[#d93025] transition-all active:scale-95 shadow-xl shadow-[#b5110e]/20"
              >
                Try Labl
              </button>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-slate-50 w-full border-t border-slate-200">
        <div className="flex flex-col md:flex-row justify-between items-center max-w-7xl mx-auto px-8 py-12">
          <div className="space-y-4 mb-8 md:mb-0">
            <div className="text-lg font-bold text-red-700">Labl</div>
            <p className="text-sm uppercase tracking-widest text-slate-500">© 2026 Labl AI. Built with Google Stitch.</p>
          </div>
          <div className="flex flex-wrap justify-center gap-10">
            <Link href="/privacy" className="text-sm uppercase tracking-widest text-slate-500 hover:text-red-700 transition-colors">
              Privacy Policy
            </Link>
            <Link href="/terms" className="text-sm uppercase tracking-widest text-slate-500 hover:text-red-700 transition-colors">
              Terms of Service
            </Link>
            <Link href="/security" className="text-sm uppercase tracking-widest text-slate-500 hover:text-red-700 transition-colors">
              Security
            </Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
