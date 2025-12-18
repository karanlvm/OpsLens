import axios from 'axios'
import { Incident, TimelineEvent, Hypothesis, EvidenceItem, Action, Runbook } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  // Incidents
  getIncidents: async (status?: string): Promise<Incident[]> => {
    const response = await client.get('/incidents', { params: { status } })
    return response.data
  },

  getIncident: async (id: string): Promise<Incident> => {
    const response = await client.get(`/incidents/${id}`)
    return response.data
  },

  createIncident: async (data: { title: string; description?: string; severity?: string }): Promise<Incident> => {
    const response = await client.post('/incidents', data)
    return response.data
  },

  getIncidentTimeline: async (id: string): Promise<TimelineEvent[]> => {
    const response = await client.get(`/incidents/${id}/timeline`)
    return response.data
  },

  generateTimeline: async (id: string): Promise<void> => {
    await client.post(`/incidents/${id}/generate-timeline`)
  },

  generateHypotheses: async (id: string): Promise<void> => {
    await client.post(`/incidents/${id}/generate-hypotheses`)
  },

  generatePostmortem: async (id: string): Promise<void> => {
    await client.post(`/incidents/${id}/generate-postmortem`)
  },

  // Evidence
  getIncidentEvidence: async (incidentId: string, evidenceType?: string): Promise<EvidenceItem[]> => {
    const response = await client.get(`/evidence/incident/${incidentId}`, {
      params: { evidence_type: evidenceType },
    })
    return response.data
  },

  uploadScreenshot: async (incidentId: string, file: File): Promise<EvidenceItem> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await client.post(`/evidence/incident/${incidentId}/upload-screenshot`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Hypotheses
  getIncidentHypotheses: async (incidentId: string): Promise<Hypothesis[]> => {
    const response = await client.get(`/hypotheses/incident/${incidentId}`)
    return response.data
  },

  updateHypothesisStatus: async (hypothesisId: string, status: string): Promise<void> => {
    await client.patch(`/hypotheses/${hypothesisId}/status`, null, {
      params: { status },
    })
  },

  // Actions
  getIncidentActions: async (incidentId: string): Promise<Action[]> => {
    const response = await client.get(`/runbooks/incident/${incidentId}/actions`)
    return response.data
  },

  completeAction: async (incidentId: string, actionId: string): Promise<void> => {
    await client.post(`/runbooks/incident/${incidentId}/actions/${actionId}/complete`)
  },

  // Runbooks
  searchRunbooks: async (query: string, service?: string): Promise<Runbook[]> => {
    const response = await client.get('/runbooks/search', {
      params: { query, service },
    })
    return response.data
  },
}

