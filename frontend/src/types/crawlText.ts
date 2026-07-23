export type CrawlSource = 'notion' | 'discord'

export interface CrawlText {
  raw_text_id: string
  source: CrawlSource
  channel: string | null
  raw_text: string
  created_at: string
}
