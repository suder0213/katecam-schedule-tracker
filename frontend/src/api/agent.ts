import { api } from './client'
import type { CrawlSource, CrawlText } from '../types/crawlText'
import type { ScheduleProposal } from '../types/scheduleProposal'

export async function createCrawlText(payload: {
  source: CrawlSource
  channel?: string
  raw_text: string
}): Promise<CrawlText> {
  return api.post<CrawlText>('/crawl-texts', payload)
}

export async function getCrawlText(rawTextId: string): Promise<CrawlText> {
  return api.get<CrawlText>(`/crawl-texts/${rawTextId}`)
}

export async function analyzeCrawlText(rawTextId: string): Promise<ScheduleProposal[]> {
  return api.post<ScheduleProposal[]>(`/crawl-texts/${rawTextId}/analyze`)
}

export async function listProposals(): Promise<ScheduleProposal[]> {
  return api.get<ScheduleProposal[]>('/schedule-proposals')
}

export async function approveProposal(proposalId: string): Promise<ScheduleProposal> {
  return api.post<ScheduleProposal>(`/schedule-proposals/${proposalId}/approve`)
}

export async function rejectProposal(proposalId: string): Promise<ScheduleProposal> {
  return api.post<ScheduleProposal>(`/schedule-proposals/${proposalId}/reject`)
}
