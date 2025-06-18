'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { Profile } from '@/lib/supabase'

interface ProfileModalProps {
  isOpen: boolean
  onClose: () => void
  isNewProfile?: boolean
}

export default function ProfileModal({ isOpen, onClose, isNewProfile = false }: ProfileModalProps) {
  const { profile, updateProfile } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    name: '',
    title: '',
    level: '',
    team: '',
    years_experience: '',
    years_at_company: '',
    specialization: '',
    tech_skills: '',
    current_projects: '',
    career_goals: '',
    biggest_challenges: '',
    strengths: '',
    learning_goals: '',
    communication_style: '',
    feedback_frequency: '',
    meeting_style: ''
  })

  useEffect(() => {
    if (profile && !isNewProfile) {
      setFormData({
        name: profile.name || '',
        title: profile.title || '',
        level: profile.level || '',
        team: profile.team || '',
        years_experience: profile.years_experience?.toString() || '',
        years_at_company: profile.years_at_company?.toString() || '',
        specialization: profile.specialization || '',
        tech_skills: profile.tech_skills?.join(', ') || '',
        current_projects: profile.current_projects?.join(', ') || '',
        career_goals: profile.career_goals?.join(', ') || '',
        biggest_challenges: profile.biggest_challenges?.join(', ') || '',
        strengths: profile.strengths?.join(', ') || '',
        learning_goals: profile.learning_goals?.join(', ') || '',
        communication_style: profile.communication_style || '',
        feedback_frequency: profile.feedback_frequency || '',
        meeting_style: profile.meeting_style || ''
      })
    }
  }, [profile, isNewProfile])

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const splitToArray = (value: string) => 
        value.split(',').map(item => item.trim()).filter(item => item.length > 0)

      const profileData: Partial<Profile> = {
        name: formData.name,
        title: formData.title,
        level: formData.level || null,
        team: formData.team || null,
        years_experience: formData.years_experience ? parseInt(formData.years_experience) : null,
        years_at_company: formData.years_at_company ? parseInt(formData.years_at_company) : null,
        specialization: formData.specialization,
        tech_skills: splitToArray(formData.tech_skills),
        current_projects: splitToArray(formData.current_projects),
        career_goals: splitToArray(formData.career_goals),
        biggest_challenges: splitToArray(formData.biggest_challenges),
        strengths: splitToArray(formData.strengths),
        learning_goals: splitToArray(formData.learning_goals),
        communication_style: formData.communication_style || null,
        feedback_frequency: formData.feedback_frequency || null,
        meeting_style: formData.meeting_style || null,
        profile_completed: true
      }

      const { error } = await updateProfile(profileData)

      if (error) {
        setError(error.message)
      } else {
        onClose()
      }
    } catch (err) {
      setError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 border border-gray-700 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Terminal-style header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <div className="flex space-x-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
          <div className="text-sm font-mono font-medium text-gray-200">
            emreq profile
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-200 text-lg">×</button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {/* Terminal-style command */}
          <div className="mb-6">
            <div className="text-green-400 font-mono text-sm mb-2">
              $ emreq profile {isNewProfile ? 'setup' : 'edit'}
            </div>
            <div className="text-gray-400 font-mono text-sm">
              {isNewProfile ? 'Set up your engineering profile' : 'Update your profile'}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Information */}
            <div>
              <h3 className="text-blue-400 font-mono text-sm mb-4 border-b border-gray-700 pb-2">
                👤 Basic Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                    placeholder="Alex Smith"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Title *</label>
                  <select
                    value={formData.title}
                    onChange={(e) => handleInputChange('title', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                    required
                  >
                    <option value="">Select title</option>
                    <option value="Software Engineer">Software Engineer</option>
                    <option value="Senior Software Engineer">Senior Software Engineer</option>
                    <option value="Staff Software Engineer">Staff Software Engineer</option>
                    <option value="Principal Engineer">Principal Engineer</option>
                    <option value="Tech Lead">Tech Lead</option>
                    <option value="Frontend Engineer">Frontend Engineer</option>
                    <option value="Backend Engineer">Backend Engineer</option>
                    <option value="Full Stack Engineer">Full Stack Engineer</option>
                    <option value="DevOps Engineer">DevOps Engineer</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Level</label>
                  <select
                    value={formData.level}
                    onChange={(e) => handleInputChange('level', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                  >
                    <option value="">Select level</option>
                    <option value="Junior">Junior</option>
                    <option value="Mid">Mid-level</option>
                    <option value="Senior">Senior</option>
                    <option value="Staff">Staff</option>
                    <option value="Principal">Principal</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Specialization *</label>
                  <select
                    value={formData.specialization}
                    onChange={(e) => handleInputChange('specialization', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                    required
                  >
                    <option value="">Select specialization</option>
                    <option value="Frontend">Frontend</option>
                    <option value="Backend">Backend</option>
                    <option value="Full-stack">Full-stack</option>
                    <option value="DevOps">DevOps/Infrastructure</option>
                    <option value="Mobile">Mobile</option>
                    <option value="Data">Data Engineering</option>
                    <option value="Machine Learning">Machine Learning</option>
                    <option value="Security">Security</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Experience */}
            <div>
              <h3 className="text-blue-400 font-mono text-sm mb-4 border-b border-gray-700 pb-2">
                💼 Experience
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Years Experience</label>
                  <input
                    type="number"
                    value={formData.years_experience}
                    onChange={(e) => handleInputChange('years_experience', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                    min="0"
                    max="50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Years at Company</label>
                  <input
                    type="number"
                    value={formData.years_at_company}
                    onChange={(e) => handleInputChange('years_at_company', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                    min="0"
                    max="50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Team</label>
                  <input
                    type="text"
                    value={formData.team}
                    onChange={(e) => handleInputChange('team', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                    placeholder="Engineering Platform"
                  />
                </div>
              </div>
            </div>

            {/* Skills & Projects */}
            <div>
              <h3 className="text-blue-400 font-mono text-sm mb-4 border-b border-gray-700 pb-2">
                🛠️ Skills & Projects
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Tech Skills (comma-separated)</label>
                  <input
                    type="text"
                    value={formData.tech_skills}
                    onChange={(e) => handleInputChange('tech_skills', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                    placeholder="React, TypeScript, Node.js, Python"
                  />
                </div>
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Current Projects (comma-separated)</label>
                  <input
                    type="text"
                    value={formData.current_projects}
                    onChange={(e) => handleInputChange('current_projects', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                    placeholder="User Dashboard Redesign, API Migration"
                  />
                </div>
              </div>
            </div>

            {/* Goals & Development */}
            <div>
              <h3 className="text-blue-400 font-mono text-sm mb-4 border-b border-gray-700 pb-2">
                🎯 Goals & Development
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Career Goals (comma-separated)</label>
                  <input
                    type="text"
                    value={formData.career_goals}
                    onChange={(e) => handleInputChange('career_goals', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                    placeholder="Tech Lead, System Architecture, Team Management"
                  />
                </div>
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Learning Goals (comma-separated)</label>
                  <input
                    type="text"
                    value={formData.learning_goals}
                    onChange={(e) => handleInputChange('learning_goals', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                    placeholder="Kubernetes, Machine Learning, Leadership Skills"
                  />
                </div>
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Biggest Challenges (comma-separated)</label>
                  <input
                    type="text"
                    value={formData.biggest_challenges}
                    onChange={(e) => handleInputChange('biggest_challenges', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                    placeholder="Time management, Code reviews, Technical debt"
                  />
                </div>
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Strengths (comma-separated)</label>
                  <input
                    type="text"
                    value={formData.strengths}
                    onChange={(e) => handleInputChange('strengths', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                    placeholder="Problem solving, Communication, Mentoring"
                  />
                </div>
              </div>
            </div>

            {/* Communication Preferences */}
            <div>
              <h3 className="text-blue-400 font-mono text-sm mb-4 border-b border-gray-700 pb-2">
                💬 Communication Preferences
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Communication Style</label>
                  <select
                    value={formData.communication_style}
                    onChange={(e) => handleInputChange('communication_style', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                  >
                    <option value="">Select style</option>
                    <option value="Direct">Direct</option>
                    <option value="Collaborative">Collaborative</option>
                    <option value="Supportive">Supportive</option>
                    <option value="Analytical">Analytical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Feedback Frequency</label>
                  <select
                    value={formData.feedback_frequency}
                    onChange={(e) => handleInputChange('feedback_frequency', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                  >
                    <option value="">Select frequency</option>
                    <option value="Weekly">Weekly</option>
                    <option value="Bi-weekly">Bi-weekly</option>
                    <option value="Monthly">Monthly</option>
                    <option value="As needed">As needed</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-mono text-gray-300 mb-2">Meeting Style</label>
                  <select
                    value={formData.meeting_style}
                    onChange={(e) => handleInputChange('meeting_style', e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                  >
                    <option value="">Select style</option>
                    <option value="Structured">Structured</option>
                    <option value="Casual">Casual</option>
                    <option value="Goal-oriented">Goal-oriented</option>
                    <option value="Flexible">Flexible</option>
                  </select>
                </div>
              </div>
            </div>

            {error && (
              <div className="text-red-400 font-mono text-sm bg-red-900/20 border border-red-800 rounded px-3 py-2">
                Error: {error}
              </div>
            )}

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-gray-900 border border-green-600 disabled:border-gray-600 rounded px-4 py-2 font-mono text-sm transition-colors"
              >
                {loading ? 'Saving...' : (isNewProfile ? 'Complete Setup' : 'Update Profile')}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600 rounded font-mono text-sm transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
