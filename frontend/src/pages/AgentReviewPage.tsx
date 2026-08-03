import { useEffect, useMemo, useRef, useState } from 'react'
import * as agentApi from '../api/agent'
import { AppHeader } from '../components/AppHeader'
import type { CrawlSource, CrawlText } from '../types/crawlText'
import type { ScheduleProposal } from '../types/scheduleProposal'
import type { UserBrief } from '../types/user'

function actorName(actor: UserBrief | null): string | null {
  if (!actor) return null
  return actor.nick_name ?? actor.email
}

const STATUS_LABEL: Record<ScheduleProposal['status'], string> = {
  pending: '대기중',
  approved: '승인됨',
  rejected: '거절됨',
}

function formatDeadline(iso: string): string {
  const d = new Date(iso)
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${hh}:${mm}`
}

function toDatetimeLocalValue(iso: string): string {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function AgentReviewPage() {
  const [source, setSource] = useState<CrawlSource>('notion')
  const [channel, setChannel] = useState('')
  const [rawText, setRawText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const [proposals, setProposals] = useState<ScheduleProposal[]>([])
  const [crawlTexts, setCrawlTexts] = useState<Record<string, CrawlText>>({})
  const [listError, setListError] = useState<string | null>(null)
  const [actionPendingId, setActionPendingId] = useState<string | null>(null)

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editContents, setEditContents] = useState('')
  const [editDeadline, setEditDeadline] = useState('')
  const [editError, setEditError] = useState<string | null>(null)

  const itemRefs = useRef<Record<string, HTMLLIElement | null>>({})

  function scrollToProposal(proposalId: string) {
    itemRefs.current[proposalId]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  function loadProposals() {
    agentApi
      .listProposals()
      .then(setProposals)
      .catch(() => setListError('제안 목록을 불러오지 못했습니다.'))
  }

  useEffect(() => {
    loadProposals()
  }, [])

  useEffect(() => {
    const missingIds = [...new Set(proposals.map((p) => p.raw_text_id))].filter(
      (id) => !crawlTexts[id],
    )
    if (missingIds.length === 0) return

    let cancelled = false
    Promise.all(missingIds.map((id) => agentApi.getCrawlText(id)))
      .then((texts) => {
        if (cancelled) return
        setCrawlTexts((prev) => {
          const next = { ...prev }
          for (const text of texts) next[text.raw_text_id] = text
          return next
        })
      })
      .catch(() => {
        if (!cancelled) setListError('원문 텍스트를 불러오지 못했습니다.')
      })
    return () => {
      cancelled = true
    }
  }, [proposals, crawlTexts])

  const groups = useMemo(() => {
    const byRawTextId = new Map<string, ScheduleProposal[]>()
    for (const p of proposals) {
      const list = byRawTextId.get(p.raw_text_id) ?? []
      list.push(p)
      byRawTextId.set(p.raw_text_id, list)
    }
    return [...byRawTextId.entries()].sort(([, a], [, b]) =>
      b[0].created_at.localeCompare(a[0].created_at),
    )
  }, [proposals])

  const pendingProposals = useMemo(
    () =>
      proposals
        .filter((p) => p.status === 'pending')
        .sort((a, b) => a.deadline.localeCompare(b.deadline)),
    [proposals],
  )

  async function handleSubmit() {
    setFormError(null)
    if (!rawText.trim()) {
      setFormError('원문 텍스트를 입력하세요.')
      return
    }
    if (source === 'discord' && !channel.trim()) {
      setFormError('Discord는 채널을 입력해야 합니다.')
      return
    }

    setIsSubmitting(true)
    try {
      const crawlText = await agentApi.createCrawlText({
        source,
        channel: source === 'discord' ? channel.trim() : undefined,
        raw_text: rawText,
      })
      await agentApi.analyzeCrawlText(crawlText.raw_text_id)
      setRawText('')
      setChannel('')
      loadProposals()
    } catch {
      setFormError('분석에 실패했습니다.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleApprove(proposal: ScheduleProposal) {
    setActionPendingId(proposal.proposal_id)
    try {
      await agentApi.approveProposal(proposal.proposal_id)
      loadProposals()
    } catch {
      setListError('승인에 실패했습니다.')
    } finally {
      setActionPendingId(null)
    }
  }

  async function handleReject(proposal: ScheduleProposal) {
    setActionPendingId(proposal.proposal_id)
    try {
      await agentApi.rejectProposal(proposal.proposal_id)
      loadProposals()
    } catch {
      setListError('거절에 실패했습니다.')
    } finally {
      setActionPendingId(null)
    }
  }

  function startEditing(proposal: ScheduleProposal) {
    setEditingId(proposal.proposal_id)
    setEditTitle(proposal.title)
    setEditContents(proposal.contents)
    setEditDeadline(toDatetimeLocalValue(proposal.deadline))
    setEditError(null)
  }

  async function handleSaveEdit(proposal: ScheduleProposal) {
    setEditError(null)
    if (!editTitle.trim() || !editContents.trim() || !editDeadline) {
      setEditError('모든 항목을 입력하세요.')
      return
    }
    setActionPendingId(proposal.proposal_id)
    try {
      await agentApi.updateProposal(proposal.proposal_id, {
        title: editTitle.trim(),
        contents: editContents.trim(),
        deadline: new Date(editDeadline).toISOString(),
      })
      setEditingId(null)
      loadProposals()
    } catch {
      setEditError('수정에 실패했습니다.')
    } finally {
      setActionPendingId(null)
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-neutral-50">
      <AppHeader />
      <div className="mx-auto flex w-full max-w-5xl gap-6 p-6">
        <div className="min-w-0 flex-1">
        <h2 className="mb-4 text-lg font-bold text-kakao-black">Agent 검토</h2>

        <div className="mb-6 rounded-xl border border-neutral-200 bg-white p-4">
          <div className="mb-3 flex gap-2">
            <select
              value={source}
              onChange={(e) => setSource(e.target.value as CrawlSource)}
              className="rounded-lg border border-neutral-200 px-2 py-1.5 text-sm"
            >
              <option value="notion">Notion</option>
              <option value="discord">Discord</option>
            </select>
            {source === 'discord' && (
              <input
                type="text"
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
                placeholder="채널명 (예: 공지방)"
                className="flex-1 rounded-lg border border-neutral-200 px-3 py-1.5 text-sm"
              />
            )}
          </div>
          <textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder="원문 텍스트를 붙여넣으세요"
            rows={6}
            className="w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm"
          />
          {formError && <p className="mt-2 text-sm text-red-500">{formError}</p>}
          <button
            type="button"
            onClick={() => void handleSubmit()}
            disabled={isSubmitting}
            className="mt-3 rounded-lg bg-kakao-yellow px-4 py-2 text-sm font-semibold text-kakao-black transition hover:bg-kakao-yellow-dark disabled:opacity-50"
          >
            {isSubmitting ? '분석 중...' : '분석 요청'}
          </button>
        </div>

        {listError && <p className="mb-3 text-sm text-red-500">{listError}</p>}

        {groups.length === 0 && (
          <p className="text-sm text-neutral-400">아직 제안된 일정이 없습니다.</p>
        )}

        <div className="flex flex-col gap-4">
          {groups.map(([rawTextId, group]) => (
            <div key={rawTextId} className="rounded-xl border border-neutral-200 bg-white p-4">
              <p className="mb-1 whitespace-pre-wrap rounded-lg bg-neutral-50 p-3 text-xs text-neutral-500">
                {crawlTexts[rawTextId]?.raw_text ?? '원문 불러오는 중...'}
              </p>
              {actorName(crawlTexts[rawTextId]?.created_by ?? null) && (
                <p className="mb-3 text-xs text-neutral-400">
                  제출: {actorName(crawlTexts[rawTextId]?.created_by ?? null)}
                </p>
              )}
              <ul className="flex flex-col gap-2">
                {group.map((p) =>
                  editingId === p.proposal_id ? (
                    <li
                      key={p.proposal_id}
                      ref={(el) => {
                        itemRefs.current[p.proposal_id] = el
                      }}
                      className="flex flex-col gap-2 rounded-lg border border-kakao-yellow-dark px-3 py-2"
                    >
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        placeholder="제목"
                        className="rounded-lg border border-neutral-200 px-2 py-1 text-sm"
                      />
                      <textarea
                        value={editContents}
                        onChange={(e) => setEditContents(e.target.value)}
                        placeholder="내용"
                        rows={2}
                        className="rounded-lg border border-neutral-200 px-2 py-1 text-sm"
                      />
                      <input
                        type="datetime-local"
                        value={editDeadline}
                        onChange={(e) => setEditDeadline(e.target.value)}
                        className="rounded-lg border border-neutral-200 px-2 py-1 text-sm"
                      />
                      {editError && <p className="text-xs text-red-500">{editError}</p>}
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setEditingId(null)}
                          className="rounded-lg border border-neutral-200 px-2.5 py-1 text-xs text-neutral-500 hover:bg-neutral-100"
                        >
                          취소
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleSaveEdit(p)}
                          disabled={actionPendingId === p.proposal_id}
                          className="rounded-lg bg-kakao-yellow px-2.5 py-1 text-xs font-semibold text-kakao-black hover:bg-kakao-yellow-dark disabled:opacity-50"
                        >
                          저장
                        </button>
                      </div>
                    </li>
                  ) : (
                    <li
                      key={p.proposal_id}
                      ref={(el) => {
                        itemRefs.current[p.proposal_id] = el
                      }}
                      className="flex items-center justify-between rounded-lg border border-neutral-100 px-3 py-2"
                    >
                      <div>
                        <p className="font-medium text-kakao-black">{p.title}</p>
                        <p className="text-xs text-neutral-500">{p.contents}</p>
                        <p className="text-xs text-neutral-400">{formatDeadline(p.deadline)}</p>
                        {p.status !== 'pending' && actorName(p.decided_by) && (
                          <p className="text-xs text-neutral-400">
                            {p.status === 'approved' ? '승인' : '거절'}: {actorName(p.decided_by)}
                          </p>
                        )}
                        {p.status === 'pending' && actorName(p.updated_by) && (
                          <p className="text-xs text-neutral-400">수정: {actorName(p.updated_by)}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                            p.status === 'approved'
                              ? 'bg-green-100 text-green-700'
                              : p.status === 'rejected'
                                ? 'bg-red-100 text-red-600'
                                : 'bg-neutral-100 text-neutral-600'
                          }`}
                        >
                          {STATUS_LABEL[p.status]}
                        </span>
                        {p.status === 'pending' && (
                          <>
                            <button
                              type="button"
                              onClick={() => startEditing(p)}
                              disabled={actionPendingId === p.proposal_id}
                              className="rounded-lg border border-neutral-200 px-2.5 py-1 text-xs text-neutral-500 hover:bg-neutral-100 disabled:opacity-50"
                            >
                              수정
                            </button>
                            <button
                              type="button"
                              onClick={() => void handleApprove(p)}
                              disabled={actionPendingId === p.proposal_id}
                              className="rounded-lg bg-kakao-yellow px-2.5 py-1 text-xs font-semibold text-kakao-black hover:bg-kakao-yellow-dark disabled:opacity-50"
                            >
                              승인
                            </button>
                            <button
                              type="button"
                              onClick={() => void handleReject(p)}
                              disabled={actionPendingId === p.proposal_id}
                              className="rounded-lg border border-neutral-200 px-2.5 py-1 text-xs text-neutral-500 hover:bg-neutral-100 disabled:opacity-50"
                            >
                              거절
                            </button>
                          </>
                        )}
                      </div>
                    </li>
                  ),
                )}
              </ul>
            </div>
          ))}
        </div>
        </div>

        <aside className="w-56 shrink-0">
          <div className="sticky top-6 rounded-xl border border-neutral-200 bg-white p-3">
            <p className="mb-2 text-sm font-bold text-kakao-black">대기중 ({pendingProposals.length})</p>
            {pendingProposals.length === 0 ? (
              <p className="text-xs text-neutral-400">대기중인 제안이 없습니다.</p>
            ) : (
              <ul className="flex flex-col gap-1">
                {pendingProposals.map((p) => (
                  <li key={p.proposal_id}>
                    <button
                      type="button"
                      onClick={() => scrollToProposal(p.proposal_id)}
                      className="w-full rounded-lg px-2 py-1.5 text-left text-xs hover:bg-neutral-100"
                    >
                      <p className="truncate font-medium text-kakao-black">{p.title}</p>
                      <p className="text-neutral-400">{formatDeadline(p.deadline)}</p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}
