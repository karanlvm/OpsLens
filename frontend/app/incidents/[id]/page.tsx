'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { format } from 'date-fns'
import { Clock, AlertCircle, Lightbulb, FileText, CheckCircle, Play } from 'lucide-react'
import { Incident, TimelineEvent, Hypothesis, EvidenceItem, Action } from '@/lib/types'
import { api } from '@/lib/api'

export default function IncidentDetailPage() {
  const params = useParams()
  const incidentId = params.id as string

  const [incident, setIncident] = useState<Incident | null>(null)
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([])
  const [evidence, setEvidence] = useState<EvidenceItem[]>([])
  const [actions, setActions] = useState<Action[]>([])
  const [activeTab, setActiveTab] = useState<'timeline' | 'hypotheses' | 'evidence' | 'actions'>('timeline')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (incidentId) {
      fetchData()
    }
  }, [incidentId])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [incidentData, timelineData, hypothesesData, evidenceData, actionsData] = await Promise.all([
        api.getIncident(incidentId),
        api.getIncidentTimeline(incidentId),
        api.getIncidentHypotheses(incidentId),
        api.getIncidentEvidence(incidentId),
        api.getIncidentActions(incidentId),
      ])
      setIncident(incidentData)
      setTimeline(timelineData)
      setHypotheses(hypothesesData)
      setEvidence(evidenceData)
      setActions(actionsData)
    } catch (error) {
      console.error('Error fetching incident data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateTimeline = async () => {
    try {
      await api.generateTimeline(incidentId)
      setTimeout(fetchData, 2000) // Refresh after a delay
    } catch (error) {
      console.error('Error generating timeline:', error)
    }
  }

  const handleGenerateHypotheses = async () => {
    try {
      await api.generateHypotheses(incidentId)
      setTimeout(fetchData, 2000)
    } catch (error) {
      console.error('Error generating hypotheses:', error)
    }
  }

  const handleCompleteAction = async (actionId: string) => {
    try {
      await api.completeAction(incidentId, actionId)
      fetchData()
    } catch (error) {
      console.error('Error completing action:', error)
    }
  }

  if (loading || !incident) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">Loading incident...</div>
      </div>
    )
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800'
      case 'high':
        return 'bg-orange-100 text-orange-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'low':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900">{incident.title}</h1>
            {incident.description && (
              <p className="mt-2 text-gray-600">{incident.description}</p>
            )}
            <div className="mt-4 flex items-center space-x-4 text-sm text-gray-500">
              <div className="flex items-center">
                <Clock className="h-4 w-4 mr-1" />
                Created: {format(new Date(incident.created_at), 'MMM d, yyyy HH:mm')}
              </div>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(incident.severity)}`}>
                {incident.severity}
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                {incident.status}
              </span>
            </div>
          </div>
          <div className="ml-4 flex space-x-2">
            <button
              onClick={handleGenerateTimeline}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm"
            >
              <Play className="h-4 w-4 inline mr-1" />
              Generate Timeline
            </button>
            <button
              onClick={handleGenerateHypotheses}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm"
            >
              <Lightbulb className="h-4 w-4 inline mr-1" />
              Generate Hypotheses
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'timeline', label: 'Timeline', icon: Clock },
            { id: 'hypotheses', label: 'Hypotheses', icon: Lightbulb },
            { id: 'evidence', label: 'Evidence', icon: FileText },
            { id: 'actions', label: 'Actions', icon: CheckCircle },
          ].map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
              >
                <Icon className="h-4 w-4 mr-2" />
                {tab.label}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg shadow">
        {activeTab === 'timeline' && (
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Timeline Events</h2>
            {timeline.length === 0 ? (
              <p className="text-gray-500">No timeline events yet.</p>
            ) : (
              <div className="space-y-4">
                {timeline.map((event) => (
                  <div key={event.id} className="border-l-4 border-primary-500 pl-4 py-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">{event.title}</h3>
                        {event.description && (
                          <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                        )}
                        <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                          <span>{format(new Date(event.timestamp), 'MMM d, HH:mm')}</span>
                          {event.source && <span>Source: {event.source}</span>}
                          <span className="px-2 py-0.5 bg-gray-100 rounded">{event.event_type}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'hypotheses' && (
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Root Cause Hypotheses</h2>
            {hypotheses.length === 0 ? (
              <p className="text-gray-500">No hypotheses generated yet. Click "Generate Hypotheses" to create them.</p>
            ) : (
              <div className="space-y-4">
                {hypotheses.map((hypothesis) => (
                  <div key={hypothesis.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{hypothesis.title}</h3>
                        <p className="text-sm text-gray-600 mt-2">{hypothesis.description}</p>
                        <div className="mt-3 flex items-center space-x-4">
                          <span className="text-xs text-gray-500">
                            Confidence: {(hypothesis.confidence * 100).toFixed(0)}%
                          </span>
                          <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">{hypothesis.status}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'evidence' && (
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Evidence</h2>
            {evidence.length === 0 ? (
              <p className="text-gray-500">No evidence items yet.</p>
            ) : (
              <div className="space-y-4">
                {evidence.map((item) => (
                  <div key={item.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{item.title}</h3>
                        <p className="text-xs text-gray-500 mt-1">
                          Type: {item.evidence_type} | Source: {item.source || 'N/A'}
                        </p>
                        {item.content && (
                          <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">{item.content}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'actions' && (
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Action Items</h2>
            {actions.length === 0 ? (
              <p className="text-gray-500">No actions yet.</p>
            ) : (
              <div className="space-y-4">
                {actions.map((action) => (
                  <div key={action.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h3 className="font-medium text-gray-900">{action.title}</h3>
                          {action.status === 'completed' && (
                            <CheckCircle className="h-5 w-5 text-green-500" />
                          )}
                        </div>
                        {action.description && (
                          <p className="text-sm text-gray-600 mt-1">{action.description}</p>
                        )}
                        <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                          <span>Type: {action.action_type || 'N/A'}</span>
                          <span className="px-2 py-0.5 bg-gray-100 rounded">{action.status}</span>
                        </div>
                      </div>
                      {action.status !== 'completed' && (
                        <button
                          onClick={() => handleCompleteAction(action.id)}
                          className="ml-4 px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                        >
                          Mark Complete
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

