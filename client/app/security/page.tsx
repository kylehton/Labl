import Link from "next/link"

export const metadata = {
  title: "Security — Labl",
  description: "How Labl protects your data and inbox.",
}

export default function Security() {
  return (
    <div className="min-h-screen bg-[#f8f9fa] text-[#191c1d]" style={{ fontFamily: "'Manrope', sans-serif" }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&display=swap');`}</style>

      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100">
        <div className="flex justify-between items-center max-w-7xl mx-auto px-6 h-16">
          <Link href="/landing-page" className="text-3xl font-black tracking-tighter text-red-700">Labl</Link>
          <div className="flex items-center gap-6">
            <Link href="/privacy" className="text-sm font-medium text-slate-500 hover:text-red-600 transition-colors tracking-tight">Privacy</Link>
            <Link href="/terms" className="text-sm font-medium text-slate-500 hover:text-red-600 transition-colors tracking-tight">Terms</Link>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-24">
        {/* Header */}
        <div className="max-w-3xl mx-auto px-6 mb-20 space-y-4">
          <span className="inline-block py-1 px-3 rounded-full bg-[#ffdad5] text-[#410001] text-xs font-bold tracking-widest uppercase">
            Trust & Safety
          </span>
          <h1 className="text-5xl font-extrabold tracking-tighter leading-tight text-[#191c1d]">Security at Labl</h1>
          <p className="text-xl text-slate-500 font-light leading-relaxed max-w-2xl">
            Security isn&apos;t a feature we added — it&apos;s the reason Labl was built the way it was. Here&apos;s exactly how we protect your inbox and your data.
          </p>
        </div>

        {/* Security pillars */}
        <section className="bg-[#f3f4f5] py-20 mb-20">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-slate-200/40">
            {[
              {
                icon: <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>,
                title: "No Email Body Storage",
                body: "Our Gmail OAuth scope only requests subject lines email body content. We do use your email body during embedding — it is never stored to our database.",
              },
              {
                icon: <path d="M15 9H9v6h6V9zm-2 4h-2v-2h2v2zm8-2V9h-2V7c0-1.1-.9-2-2-2h-2V3h-2v2h-2V3H9v2H7c-1.1 0-2 .9-2 2v2H3v2h2v2H3v2h2v2c0 1.1.9 2 2 2h2v2h2v-2h2v2h2v-2h2c1.1 0 2-.9 2-2v-2h2v-2h-2v-2h2zm-4 6H7V7h10v10z"/>,
                title: "Local ML Inference",
                body: "Classification runs entirely on our own servers. Your email metadata and contents are never sent to OpenAI, Anthropic, Google AI, or any third-party model provider.",
              },
              {
                icon: <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>,
                title: "Encryption of Sensitive Tokens",
                body: "OAuth credentials, access tokens, and refresh tokens are encrypted. These are never logged.",
              },
              {
                icon: <path d="M12.65 10C11.83 7.67 9.61 6 7 6c-3.31 0-6 2.69-6 6s2.69 6 6 6c2.61 0 4.83-1.67 5.65-4H17v4h4v-4h2v-4H12.65zM7 14c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/>,
                title: "OAuth, Not Passwords",
                body: "We use Google's official OAuth 2.0 flow. We never see, ask for, or store your Google password. You can revoke access from your Google Account at any time.",
              },
              {
                icon: <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>,
                title: "Minimal Data Retention",
                body: "We store only vector embeddings and label records — not raw subject lines. Embeddings are opaque numerical representations that cannot be meaningfully reversed.",
              },
              {
                icon: <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>,
                title: "Rate Limiting",
                body: "API endpoints are rate-limited to prevent abuse and protect the integrity of your inbox data. Suspicious activity triggers automatic alerts.",
              },
            ].map((card, i) => (
              <div key={i} className="bg-[#f3f4f5] p-10 space-y-4">
                <svg className="w-8 h-8 text-[#b5110e]" fill="currentColor" viewBox="0 0 24 24">
                  {card.icon}
                </svg>
                <h3 className="text-xl font-bold tracking-tight text-[#191c1d]">{card.title}</h3>
                <p className="text-slate-500 leading-relaxed text-sm">{card.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Data flow diagram */}
        <section className="max-w-3xl mx-auto px-6 mb-20 space-y-8">
          <h2 className="text-3xl font-black tracking-tighter text-[#191c1d]">What Labl Sees vs. What It Stores</h2>
          <div className="rounded-2xl border border-slate-200 overflow-hidden">
            <div className="bg-white divide-y divide-slate-100">
              {[
                { item: "Email body content", sees: true, stores: false },
                { item: "Email subject line", sees: true, stores: false },
                { item: "Sender name & address", sees: true, stores: false },
                { item: "Vector embedding of subject/sender", sees: true, stores: true },
                { item: "Gmail message ID", sees: true, stores: true },
                { item: "Label applied + timestamp", sees: true, stores: true },
                { item: "Your Google password", sees: false, stores: false },
                { item: "OAuth access token", sees: true, stores: true },
              ].map((row, i) => (
                <div key={i} className="grid grid-cols-5 px-6 py-4 text-sm">
                  <span className="col-span-3 text-slate-600 font-medium">{row.item}</span>
                  <span className="text-center">
                    {row.sees
                      ? <svg className="w-4 h-4 text-emerald-500 mx-auto" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                      : <svg className="w-4 h-4 text-red-400 mx-auto" fill="currentColor" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                    }
                  </span>
                  <span className="text-center">
                    {row.stores
                      ? <svg className="w-4 h-4 text-emerald-500 mx-auto" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                      : <svg className="w-4 h-4 text-red-400 mx-auto" fill="currentColor" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                    }
                  </span>
                </div>
              ))}
            </div>
            <div className="bg-slate-50 grid grid-cols-5 px-6 py-3 border-t border-slate-200">
              <span className="col-span-3 text-xs font-bold uppercase tracking-widest text-slate-400">Data Point</span>
              <span className="text-xs font-bold uppercase tracking-widest text-slate-400 text-center">Accessed</span>
              <span className="text-xs font-bold uppercase tracking-widest text-slate-400 text-center">Stored</span>
            </div>
          </div>
          <p className="text-sm text-slate-400">OAuth tokens are encrypted at rest and used only to write labels back to Gmail.</p>
        </section>

        {/* Vulnerability disclosure */}
        <section className="max-w-3xl mx-auto px-6 mb-20">
          <div className="bg-white rounded-2xl border border-slate-200 p-10 space-y-4">
            <svg className="w-8 h-8 text-[#b5110e]" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/>
            </svg>
            <h2 className="text-2xl font-bold tracking-tight text-[#191c1d]">Responsible Disclosure</h2>
            <p className="text-slate-500 leading-relaxed">
              If you discover a security vulnerability in Labl, we want to hear from you. Please report it to <span className="text-[#b5110e] font-medium">khtcodes@gmail.com</span> with a description of the issue and steps to reproduce. We commit to acknowledging your report within 48 hours and keeping you informed as we work to resolve it.
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-slate-50 w-full border-t border-slate-200">
        <div className="flex flex-col md:flex-row justify-between items-center max-w-7xl mx-auto px-8 py-12">
          <div className="space-y-4 mb-8 md:mb-0">
            <div className="text-lg font-bold text-red-700">Labl</div>
            <p className="text-sm uppercase tracking-widest text-slate-500">© 2026 Labl AI.</p>
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
