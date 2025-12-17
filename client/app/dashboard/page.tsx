"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Mail, Plus, Trash2, Undo2, Tag } from "lucide-react"

export default function Dashboard() {
  const [userName] = useState("Kyle")
  const [userEmail] = useState("khtcodes@gmail.com")

  const [labels, setLabels] = useState([
    "Internship",
    "Job",
    "Rejection",
    "Acceptance",
    "School",
    "Interview",
  ])

  const [newLabel, setNewLabel] = useState("")

  const [recentEmails] = useState([
    {
      id: 1,
      subject: "Software Engineering Internship - Summer 2025",
      sender: "Meta Careers",
      action: "labeled",
      label: "Internship",
      time: "2 mins ago",
    },
    {
      id: 2,
      subject: "Your Application Status Update",
      sender: "Google Recruiting",
      action: "labeled",
      label: "Acceptance",
      time: "15 mins ago",
    },
    {
      id: 3,
      subject: "Re: Technical Interview Scheduling",
      sender: "Amazon SDE Team",
      action: "labeled",
      label: "Interview",
      time: "1 hour ago",
    },
    {
      id: 4,
      subject: "Newsletter: Tech Industry Updates",
      sender: "TechCrunch",
      action: "deleted",
      label: null,
      time: "2 hours ago",
    },
    {
      id: 5,
      subject: "Thank you for your interest",
      sender: "Microsoft Talent Team",
      action: "labeled",
      label: "Rejection",
      time: "3 hours ago",
    },
    {
      id: 6,
      subject: "Your application to Apple",
      sender: "Apple Recruiting",
      action: "labeled",
      label: "Job",
      time: "6 hours ago",
    },
    {
      id: 7,
      subject: "Promotional: 50% off courses",
      sender: "Udemy",
      action: "deleted",
      label: null,
      time: "8 hours ago",
    },
    {
      id: 8,
      subject: "Course Registration Reminder",
      sender: "Registrar Office",
      action: "labeled",
      label: "School",
      time: "10 hours ago",
    },
    {
      id: 9,
      subject: "Startup Jobs Weekly Digest",
      sender: "AngelList",
      action: "labeled",
      label: "Job",
      time: "12 hours ago",
    },
  ])

  const addLabel = () => {
    if (newLabel.trim() && !labels.includes(newLabel.trim())) {
      setLabels([...labels, newLabel.trim()])
      setNewLabel("")
    }
  }

  const removeLabel = (label: string) => {
    setLabels(labels.filter((l) => l !== label))
  }

  return (
    <main className="min-h-screen bg-black">
      {/* Header */}
      <header className="w-full border-b border-white/10 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center">
              <Mail className="w-5 h-5 text-white" />
            </div>
            <span className="text-white text-xl font-bold">GSort</span>
          </div>

          <div className="flex items-center gap-8">
            <span className="text-white font-medium hidden sm:block">Hi, {userName}</span>
            <span className="text-gray-400 text-sm">{userEmail}</span>
          </div>
        </div>
      </header>

      {/* Mobile User Greeting */}
      <div className="sm:hidden px-4 pt-6">
        <span className="text-white text-lg font-medium">Hi, {userName}</span>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Label Management Section */}
        <section className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-8 h-8 bg-red-600/20 rounded-lg flex items-center justify-center">
              <Tag className="w-4 h-4 text-red-500" />
            </div>
            <h2 className="text-white text-xl font-semibold">Auto-Label Settings</h2>
          </div>

          <p className="text-gray-400 text-sm mb-6 leading-relaxed">
            Manage labels that will be automatically applied to your inbox. Add or remove labels to customize your email
            organization.
          </p>

          {/* Add New Label */}
          <div className="flex gap-3 mb-6">
            <Input
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addLabel()}
              placeholder="Enter new label name..."
              className="bg-black border-white/20 text-white placeholder:text-gray-500 focus:border-red-600"
            />
            <Button onClick={addLabel} className="bg-red-600 hover:bg-red-700 text-white shrink-0">
              <Plus className="w-4 h-4 mr-2" />
              Add Label
            </Button>
          </div>

          {/* Labels Grid */}
          <div className="flex flex-wrap gap-3">
            {labels.map((label) => (
              <div
                key={label}
                className="flex items-center gap-2 bg-black/50 border border-white/10 rounded-lg px-4 py-2 group hover:border-red-600/50 transition-colors"
              >
                <Tag className="w-4 h-4 text-red-500" />
                <span className="text-white text-sm font-medium">{label}</span>
                <button
                  onClick={() => removeLabel(label)}
                  className="text-gray-500 hover:text-red-500 transition-colors ml-2"
                  aria-label={`Remove ${label} label`}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* Recent Activity Section */}
        <section className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-8 h-8 bg-red-600/20 rounded-lg flex items-center justify-center">
              <Mail className="w-4 h-4 text-red-500" />
            </div>
            <h2 className="text-white text-xl font-semibold">Recent Activity</h2>
          </div>

          <p className="text-gray-400 text-sm mb-6 leading-relaxed">
            Your 10 most recent emails that were automatically labeled or deleted.
          </p>

          {/* Email List */}
          <div className="space-y-3">
            {recentEmails.map((email) => (
              <div
                key={email.id}
                className="bg-black/50 border border-white/10 rounded-lg p-4 hover:border-white/20 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-white font-medium text-sm truncate">{email.subject}</h3>
                      {email.action === "labeled" && email.label && (
                        <span className="shrink-0 inline-flex items-center gap-1 bg-red-600/20 border border-red-600/30 text-red-400 px-2 py-0.5 rounded text-xs font-medium">
                          <Tag className="w-3 h-3" />
                          {email.label}
                        </span>
                      )}
                      {email.action === "deleted" && (
                        <span className="shrink-0 inline-flex items-center gap-1 bg-gray-600/20 border border-gray-600/30 text-gray-400 px-2 py-0.5 rounded text-xs font-medium">
                          <Trash2 className="w-3 h-3" />
                          Deleted
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      <span>{email.sender}</span>
                      <span>•</span>
                      <span>{email.time}</span>
                    </div>
                  </div>

                  {email.action === "labeled" && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="shrink-0 border-white/20 text-white hover:bg-white/10 hover:text-white bg-transparent"
                    >
                      <Undo2 className="w-3.5 h-3.5 mr-2" />
                      Undo
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  )
}
