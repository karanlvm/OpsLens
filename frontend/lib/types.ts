export interface Incident {
  id: string
  title: string
  description: string | null
  status: string
  severity: string
  created_at: string
  updated_at: string | null
  resolved_at: string | null
  incident_metadata: Record<string, any>
}

export interface TimelineEvent {
  id: string
  timestamp: string
  event_type: string
  title: string
  description: string | null
  source: string | null
  event_metadata: Record<string, any>
}

export interface Hypothesis {
  id: string
  title: string
  description: string
  confidence: number
  rank: number
  status: string
  supporting_evidence: string[]
  created_at: string
}

export interface EvidenceItem {
  id: string
  evidence_type: string
  title: string
  content: string | null
  source: string | null
  source_url: string | null
  file_path: string | null
  created_at: string
}

export interface Action {
  id: string
  title: string
  description: string | null
  action_type: string | null
  status: string
  created_at: string
  completed_at: string | null
}

export interface Runbook {
  id: string
  title: string
  description: string | null
  content: string
  service: string | null
  tags: string[]
}

