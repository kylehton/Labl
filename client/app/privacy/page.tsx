import Link from "next/link"

export const metadata = {
  title: "Privacy Policy — Labl",
  description: "How Labl collects, uses, and protects your data.",
}

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-[#f8f9fa] text-[#191c1d]" style={{ fontFamily: "'Manrope', sans-serif" }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&display=swap');`}</style>

      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100">
        <div className="flex justify-between items-center max-w-7xl mx-auto px-6 h-16">
          <Link href="/landing-page" className="text-3xl font-black tracking-tighter text-red-700">Labl</Link>
          <div className="flex items-center gap-6">
            <Link href="/terms" className="text-sm font-medium text-slate-500 hover:text-red-600 transition-colors tracking-tight">Terms</Link>
            <Link href="/security" className="text-sm font-medium text-slate-500 hover:text-red-600 transition-colors tracking-tight">Security</Link>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-24 max-w-3xl mx-auto px-6">
        {/* Header */}
        <div className="mb-16 space-y-4">
          <span className="inline-block py-1 px-3 rounded-full bg-[#ffdad5] text-[#410001] text-xs font-bold tracking-widest uppercase">
            Privacy
          </span>
          <h1 className="text-5xl font-extrabold tracking-tighter leading-tight text-[#191c1d]">Our Policy</h1>
          <p className="text-slate-500 text-base">Effective date: April 7, 2026</p>
        </div>

        {/* Content */}
        <div className="space-y-12 text-slate-600 leading-relaxed">

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">1. Overview</h2>
            <p>
              Labl AI (&quot;Labl&quot;, &quot;we&quot;, &quot;our&quot;) operates the Labl email labeling service. This Privacy Policy explains what information we collect when you use our service, how we use it, and the choices you have over your information.
            </p>
            <p>
              We are committed to a privacy-first architecture. The design principle behind Labl is that we minimize the email content touches our database — only the minimal metadata required to operate the labeling service is ever stored.
            </p>
          </section>

          <section className="space-y-6">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">2. Information We Collect</h2>
            <h3 className="font-semibold text-[#191c1d]">Account Information</h3>
            <p className='ml-4'>
              When you sign in with Google, we receive your name, email address, and profile picture from Google OAuth. We use this solely to identify your account.
            </p>
            <h3 className="font-semibold text-[#191c1d]">Email Metadata</h3>
            <p className='ml-4'>
              To classify your inbox, we access email subject lines and full email content via the Gmail API. <strong>We do not store your email body content.</strong>
            </p>
            <h3 className="font-semibold text-[#191c1d]">Vector Embeddings</h3>
            <p className='ml-4'>
              Subject lines and sender metadata are converted into numerical vector embeddings by our locally-run embedding model. These embeddings — <strong>not raw text</strong> — are stored in our database and used to improve label accuracy over time. They cannot be meaningfully reversed into the original subject line text.
            </p>
            <h3 className="font-semibold text-[#191c1d]">Label Records</h3>
            <p className='ml-4'>
              We store the Gmail message ID, the label applied, and a timestamp. This allows us to sync label state and provide you with label history.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">3. How We Use Your Information</h2>
            <ul className="list-none space-y-3">
              {[
                "Authenticate your account via Google OAuth.",
                "Classify your email subject lines and apply Gmail labels.",
                "Improve classification accuracy using your confirmed and rejected labels.",
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <svg className="w-4 h-4 text-[#b5110e] mt-1 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">4. What We Do Not Do</h2>
            <ul className="list-none space-y-3">
              {[
                "We do not sell your data to third parties.",
                "We do not share your email metadata with external AI providers (no OpenAI, Anthropic, or similar API calls).",
                "We do not use your data to train shared models that benefit other users.",
                "We do not store your email body content under any circumstances.",
                "We do not store raw credentials — OAuth access and refresh tokens are encrypted, expired, and cycled regularly.",
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <svg className="w-4 h-4 text-red-400 mt-1 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">5. Data Retention</h2>
            <p>
              Vector embeddings and label records are retained while your account is active. If you delete your account, all stored embeddings and label records are permanently deleted within 30 days. OAuth tokens are revoked immediately upon account deletion or manual disconnection.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">6. Your Rights</h2>
            <p>You will always have the right to:</p>
            <ul className="list-none space-y-3">
              {[
                "Access the data we hold about you upon request",
                "Request deletion of your account and associated data",
                "Revoke Gmail OAuth access at any time via your Google Account settings",
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <svg className="w-4 h-4 text-[#b5110e] mt-1 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">7. Third-Party Services</h2>
            <p>
              Labl uses the Google Gmail API to read email metadata and write labels. Your use of Google services is governed by Google&apos;s Privacy Policy. We do not use any other third-party AI or analytics services that receive your email data.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">8. Changes to This Policy</h2>
            <p>
              We may update this Privacy Policy from time to time. If we make material changes, we will notify you by email or by a prominent notice in the app at least 14 days before the changes take effect. Continued use of Labl after that date constitutes acceptance of the updated policy.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">9. Contact</h2>
            <p>
              Questions or concerns about this policy? Reach us at <span className="text-[#b5110e] font-medium">khtcodes@gmail.com</span>.
            </p>
          </section>
        </div>
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
