import Link from "next/link"

export const metadata = {
  title: "Terms of Service — Labl",
  description: "The rules and agreements governing your use of Labl.",
}

export default function TermsOfService() {
  return (
    <div className="min-h-screen bg-[#f8f9fa] text-[#191c1d]" style={{ fontFamily: "'Manrope', sans-serif" }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&display=swap');`}</style>

      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100">
        <div className="flex justify-between items-center max-w-7xl mx-auto px-6 h-16">
          <Link href="/landing-page" className="text-3xl font-black tracking-tighter text-red-700">Labl</Link>
          <div className="flex items-center gap-6">
            <Link href="/privacy" className="text-sm font-medium text-slate-500 hover:text-red-600 transition-colors tracking-tight">Privacy</Link>
            <Link href="/security" className="text-sm font-medium text-slate-500 hover:text-red-600 transition-colors tracking-tight">Security</Link>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-24 max-w-3xl mx-auto px-6">
        {/* Header */}
        <div className="mb-16 space-y-4">
          <span className="inline-block py-1 px-3 rounded-full bg-[#ffdad5] text-[#410001] text-xs font-bold tracking-widest uppercase">
            Legal
          </span>
          <h1 className="text-5xl font-extrabold tracking-tighter leading-tight text-[#191c1d]">Terms of Service</h1>
          <p className="text-slate-500 text-base">Effective date: April 7, 2026</p>
        </div>

        {/* Content */}
        <div className="space-y-12 text-slate-600 leading-relaxed">

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">1. Acceptance of Terms</h2>
            <p>
              By accessing or using Labl (&quot;the Service&quot;), you agree to be bound by these Terms of Service (&quot;Terms&quot;). If you do not agree to these Terms, do not use the Service. These Terms apply to all users of the Service.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">2. Description of Service</h2>
            <p>
              Labl is an AI-powered email labeling service that connects to your Gmail account via Google OAuth, analyzes email subject lines and sender metadata, and applies organizational labels to your inbox. The Service uses locally-run machine learning models — your email content is never shared with external AI providers.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">3. Eligibility</h2>
            <p>
              You must be at least 13 years old to use Labl. If you are under 18, you represent that you have your parent or guardian&apos;s permission to use the Service. By using Labl, you represent and warrant that you meet these eligibility requirements.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">4. Your Account</h2>
            <p>
              You are responsible for maintaining the security of your Google account. Labl accesses your Gmail account through official Google OAuth flows — we never have direct access to your Google password. You can revoke Labl&apos;s access at any time through your Google Account settings under &quot;Third-party apps with account access.&quot;
            </p>
            <p>
              You are responsible for all activity that occurs through your Labl account. If you believe your account has been compromised, contact us immediately.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">5. Acceptable Use</h2>
            <p>You agree not to:</p>
            <ul className="list-none space-y-3">
              {[
                "Use the Service for any unlawful purpose or in violation of any applicable laws",
                "Attempt to reverse-engineer, scrape, or extract data from the Labl platform",
                "Interfere with or disrupt the integrity or performance of the Service",
                "Attempt to gain unauthorized access to any part of the Service or its related systems",
                "Use the Service to process email accounts you do not own or are not authorized to access",
                "Abuse rate limits or attempt to circumvent usage restrictions",
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <svg className="w-4 h-4 text-red-400 mt-1 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">6. Intellectual Property</h2>
            
            <p>
              Your email data remains yours. We claim no ownership over any email content, metadata, or labels associated with your Gmail account.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">7. Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, Labl AI shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of, or inability to use, the Service — including but not limited to lost data, misapplied labels, or interruption of service.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">8. Disclaimer of Warranties</h2>
            <p>
              The Service is provided &quot;as is&quot; and &quot;as available&quot; without warranties of any kind, express or implied. We do not warrant that the Service will be uninterrupted, error-free, or that label classifications will be accurate in all cases. Email labeling is probabilistic by nature — review labels before relying on them for critical workflows.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">9. Termination</h2>
            <p>
              You may stop using the Service at any time and revoke Gmail access through your Google Account. We may suspend or terminate your access if we believe you have violated these Terms, without prior notice.
            </p>
          </section>


          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">10. Changes to Terms</h2>
            <p>
              We reserve the right to update these Terms at any time. We will notify you of material changes at least 14 days in advance via email or an in-app notice. Continued use of the Service after the effective date constitutes acceptance of the revised Terms.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#191c1d] tracking-tight">11. Contact</h2>
            <p>
              Questions about these Terms? Contact us at <span className="text-[#b5110e] font-medium">khtcodes@gmail.com</span>.
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
