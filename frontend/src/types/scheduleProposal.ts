export type ProposalStatus = 'pending' | 'approved' | 'rejected'

export interface ScheduleProposal {
  proposal_id: string
  raw_text_id: string
  title: string
  contents: string
  deadline: string
  status: ProposalStatus
  created_at: string
  updated_at: string
}
