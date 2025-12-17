import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Mail, Sparkles, Zap, Shield } from "lucide-react"
import { useAuth } from "../../context/AuthContext"
import { useState } from 'react'

export default function Home() {
  const { login } = useAuth();

  const handleLogin = () => {
    login();
  }

  return (
    <main className="min-h-screen bg-[#1A1A1A] flex flex-col">
      <nav className="border-b border-white/15 backdrop-blur-sm">
        <div className="w-full px-10 py-5 flex items-center justify-between">
          <div className="justify-between flex items-center gap-2">
            <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center">
              <Mail className="w-5 h-5 text-[#F6F6F6]" />
            </div>
            <span className="text-[#F6F6F6] text-xl font-bold">GSort</span>
          </div>
          <Button variant="default" onClick={handleLogin} className="bg-[#252525] text-[#F6F6F6] hover:bg-white/10">
            Sign In
          </Button>          
        </div>
      </nav>

      <section className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-red-950/30 border border-red-900/50 text-red-400 px-4 py-2 rounded-full text-sm font-medium">
            <Sparkles className="w-4 h-4" />
            <span>ML-Powered Email Intelligence</span>
          </div>

          {/* Main Heading */}
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-[#F6F6F6] tracking-tight text-balance">
            Smart Email Sorting <span className="text-red-600">for Students</span>
          </h1>

          {/* Description */}
          <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto text-pretty leading-relaxed">
            Automatically organize your inbox with AI-powered labels. GSort intelligently categorizes internships, job
            opportunities, acceptances, rejections, and more—trained specifically for CS/SWE students.
          </p>

          {/* CTA Button */}
          <div className="pt-4">
            <Button
              asChild
              size="lg"
              onClick={handleLogin}
              className="bg-red-700 hover:bg-red-600 text-[#F6F6F6] font-semibold px-8 py-6 text-lg rounded-lg shadow-lg shadow-red-600/20 transition-all hover:shadow-red-600/40"
            >
              <p>Get Started</p>
            </Button>
            <p className="text-sm text-gray-500 mt-4">No credit card required • Free to start</p>
          </div>

          {/* Feature Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-12 max-w-3xl mx-auto">
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 text-left hover:bg-white/10 transition-colors">
              <div className="w-10 h-10 bg-red-600/20 rounded-lg flex items-center justify-center mb-4">
                <Zap className="w-5 h-5 text-red-500" />
              </div>
              <h3 className="text-[#F6F6F6] font-semibold mb-2">Instant Sorting</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Automatically categorize emails as they arrive using advanced ML models
              </p>
            </div>

            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 text-left hover:bg-white/10 transition-colors">
              <div className="w-10 h-10 bg-red-600/20 rounded-lg flex items-center justify-center mb-4">
                <Sparkles className="w-5 h-5 text-red-500" />
              </div>
              <h3 className="text-[#F6F6F6] font-semibold mb-2">Student-Focused</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Trained specifically for CS/SWE students' unique email patterns
              </p>
            </div>

            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 text-left hover:bg-white/10 transition-colors">
              <div className="w-10 h-10 bg-red-600/20 rounded-lg flex items-center justify-center mb-4">
                <Shield className="w-5 h-5 text-red-500" />
              </div>
              <h3 className="text-[#F6F6F6] font-semibold mb-2">Security First</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Your mail stays safe, deleted in 30 days, giving time to retrieve them
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full border-t border-white/10 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-gray-500 text-sm">© 2025 GSort. All rights reserved.</p>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <Link href="/privacy" className="hover:text-[#F6F6F6] transition-colors">
                Privacy Policy
              </Link>
              <Link href="/terms" className="hover:text-[#F6F6F6] transition-colors">
                Terms of Service
              </Link>
              <Link href="/contact" className="hover:text-[#F6F6F6] transition-colors">
                Contact
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </main>
  )
}
