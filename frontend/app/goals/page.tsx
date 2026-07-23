"use client"

import { useMemo, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
    CheckCircle2Icon,
    AlertTriangleIcon,
    LockIcon,
    PlusIcon,
    TargetIcon,
    Trash2Icon,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { PortfolioChart } from "@/components/portfolio-chart"
import {
    type GoalDetail,
    type GoalProgress,
    addAllocation,
    createGoal,
    deleteGoal,
    fetchBreakdown,
    fetchGoal,
    fetchGoals,
    gbp,
    removeAllocation,
    sourceLabel,
} from "@/lib/portfolio"

function useGoalInvalidate() {
    const qc = useQueryClient()
    return () => {
        qc.invalidateQueries({ queryKey: ["goals"] })
        qc.invalidateQueries({ queryKey: ["goal"] })
        // Ring-fenced goals change the spendable/committed split + projections.
        qc.invalidateQueries({ queryKey: ["net-worth-breakdown"] })
        qc.invalidateQueries({ queryKey: ["projection"] })
    }
}

function StatusBadge({ goal }: { goal: GoalDetail }) {
    if (goal.reached)
        return (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                <CheckCircle2Icon className="size-3.5" /> Funded
            </span>
        )
    if (goal.overdue)
        return (
            <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/10 px-2 py-0.5 text-xs font-medium text-rose-600 dark:text-rose-400">
                <AlertTriangleIcon className="size-3.5" /> Overdue
            </span>
        )
    if (goal.on_track === true)
        return (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                <CheckCircle2Icon className="size-3.5" /> On track
            </span>
        )
    if (goal.on_track === false)
        return (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
                <AlertTriangleIcon className="size-3.5" /> Behind pace
            </span>
        )
    return (
        <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
            Tracking
        </span>
    )
}

// A source the user can earmark: its key + current value, for the dropdown.
type Source = { key: string; value: number }

function AddEarmark({
    goalId,
    sources,
    onDone,
}: {
    goalId: number
    sources: Source[]
    onDone: () => void
}) {
    const [sourceKey, setSourceKey] = useState("")
    const [amount, setAmount] = useState("")
    const [error, setError] = useState<string | null>(null)
    const invalidate = useGoalInvalidate()

    const mut = useMutation({
        mutationFn: () =>
            addAllocation(goalId, {
                source_key: sourceKey,
                allocated_amount: amount.trim() || null,
            }),
        onSuccess: () => {
            setSourceKey("")
            setAmount("")
            setError(null)
            invalidate()
            onDone()
        },
        onError: (e: Error) => setError(e.message),
    })

    if (sources.length === 0)
        return (
            <p className="text-xs text-muted-foreground">
                Every source is already earmarked to this goal.
            </p>
        )

    return (
        <div className="flex flex-wrap items-end gap-2">
            <label className="flex flex-col gap-1 text-[11px] text-muted-foreground">
                Earmark a source
                <select
                    className="h-8 rounded-md border border-input bg-background px-2 text-xs outline-none focus-visible:border-ring"
                    value={sourceKey}
                    onChange={(e) => setSourceKey(e.target.value)}
                >
                    <option value="">Select…</option>
                    {sources.map((s) => (
                        <option key={s.key} value={s.key}>
                            {sourceLabel(s.key)} ({gbp.format(s.value)})
                        </option>
                    ))}
                </select>
            </label>
            <label className="flex flex-col gap-1 text-[11px] text-muted-foreground">
                Amount (optional)
                <Input
                    className="h-8 w-28 rounded-md border border-input px-2 text-xs"
                    type="number"
                    step="any"
                    placeholder="whole balance"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                />
            </label>
            <Button
                size="xs"
                variant="secondary"
                disabled={!sourceKey || mut.isPending}
                onClick={() => mut.mutate()}
            >
                <PlusIcon /> {mut.isPending ? "Adding…" : "Earmark"}
            </Button>
            {error && <span className="text-xs text-destructive">{error}</span>}
        </div>
    )
}

function GoalCard({ summary, allSources }: { summary: GoalProgress; allSources: Source[] }) {
    const invalidate = useGoalInvalidate()
    // Detail carries the funding series + inferred run-rate the list omits.
    const { data: goal } = useQuery({
        queryKey: ["goal", summary.id],
        queryFn: () => fetchGoal(summary.id),
        // Seed instantly from the list so the card never flashes empty.
        initialData: { ...summary, series: [], actual_monthly: null, on_track: null } as GoalDetail,
    })

    const removeAllocMut = useMutation({
        mutationFn: (allocationId: number) => removeAllocation(summary.id, allocationId),
        onSuccess: invalidate,
    })
    const deleteMut = useMutation({ mutationFn: () => deleteGoal(summary.id), onSuccess: invalidate })

    const earmarkedKeys = new Set(goal.allocations.map((a) => a.source_key))
    const available = allSources.filter((s) => !earmarkedKeys.has(s.key))
    const pctWidth = goal.target > 0 ? Math.min((goal.funded / goal.target) * 100, 100) : 0
    const barColor = goal.reached
        ? "bg-emerald-500"
        : goal.on_track === false || goal.overdue
          ? "bg-amber-500"
          : "bg-sky-500"

    return (
        <Card>
            <CardHeader className="gap-2 border-b">
                <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                        <CardTitle className="flex items-center gap-2 text-base">
                            <span className="truncate">{goal.name}</span>
                            {goal.ring_fenced && (
                                <span
                                    className="inline-flex items-center gap-1 rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium text-amber-600 uppercase dark:text-amber-400"
                                    title="Ring-fenced: this money is carved out of Spendable"
                                >
                                    <LockIcon className="size-3" /> Ring-fenced
                                </span>
                            )}
                        </CardTitle>
                        <p className="mt-0.5 text-xs text-muted-foreground">
                            {goal.target_date
                                ? goal.days_remaining !== null && goal.days_remaining >= 0
                                    ? `${goal.days_remaining} days left · by ${new Date(
                                          goal.target_date,
                                      ).toLocaleDateString("en-GB", {
                                          day: "numeric",
                                          month: "short",
                                          year: "numeric",
                                      })}`
                                    : `Target date ${new Date(goal.target_date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}`
                                : "No deadline"}
                        </p>
                    </div>
                    <div className="flex items-center gap-1">
                        <StatusBadge goal={goal} />
                        <Button
                            size="icon-xs"
                            variant="ghost"
                            aria-label="Delete goal"
                            onClick={() => {
                                if (confirm(`Delete "${goal.name}"? This can't be undone.`))
                                    deleteMut.mutate()
                            }}
                        >
                            <Trash2Icon />
                        </Button>
                    </div>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Progress */}
                <div className="space-y-1.5">
                    <div className="flex items-end justify-between gap-3">
                        <span className="font-mono text-2xl font-semibold tracking-tight tabular-nums">
                            {gbp.format(goal.funded)}
                        </span>
                        <span className="text-sm text-muted-foreground">
                            of{" "}
                            <span className="font-mono tabular-nums">{gbp.format(goal.target)}</span>
                            {goal.pct !== null && (
                                <span className="ml-1 font-medium text-foreground">
                                    ({Math.round(goal.pct * 100)}%)
                                </span>
                            )}
                        </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                        <div
                            className={`h-full rounded-full ${barColor}`}
                            style={{ width: `${Math.max(pctWidth, 1)}%` }}
                        />
                    </div>
                    {!goal.reached && (
                        <p className="text-xs text-muted-foreground">
                            {gbp.format(goal.remaining)} to go
                            {goal.required_monthly !== null && (
                                <>
                                    {" · need "}
                                    <span className="font-medium text-foreground">
                                        {gbp.format(goal.required_monthly)}/mo
                                    </span>
                                </>
                            )}
                            {goal.actual_monthly !== null && (
                                <> · saving ~{gbp.format(goal.actual_monthly)}/mo</>
                            )}
                        </p>
                    )}
                </div>

                {/* Funding curve — needs at least two snapshots to draw a line. */}
                {goal.series.length >= 2 ? (
                    <PortfolioChart
                        data={goal.series.map((p) => ({ date: p.date, value: p.funded }))}
                        positive={goal.on_track !== false}
                    />
                ) : (
                    <p className="text-xs text-muted-foreground">
                        Funding curve appears once there are a couple of daily snapshots.
                    </p>
                )}

                {/* Earmarked sources */}
                <div className="space-y-2 border-t pt-3">
                    <p className="text-xs font-medium text-muted-foreground">Earmarked sources</p>
                    {goal.allocations.length === 0 && (
                        <p className="text-xs text-muted-foreground">
                            None yet — earmark a source below to start funding this goal.
                        </p>
                    )}
                    {goal.allocations.map((a) => (
                        <div
                            key={a.id}
                            className="flex items-center justify-between gap-3 text-sm"
                        >
                            <span className="min-w-0 truncate">
                                {sourceLabel(a.source_key)}
                                {a.allocated_amount !== null && (
                                    <span className="ml-1 text-xs text-muted-foreground">
                                        (slice of {gbp.format(a.allocated_amount)})
                                    </span>
                                )}
                            </span>
                            <div className="flex items-center gap-2">
                                <span className="font-mono text-sm tabular-nums">
                                    {gbp.format(a.counted)}
                                </span>
                                <Button
                                    size="icon-xs"
                                    variant="ghost"
                                    aria-label="Remove earmark"
                                    onClick={() => removeAllocMut.mutate(a.id)}
                                >
                                    <Trash2Icon />
                                </Button>
                            </div>
                        </div>
                    ))}
                    <AddEarmark goalId={goal.id} sources={available} onDone={() => {}} />
                </div>
            </CardContent>
        </Card>
    )
}

export default function GoalsPage() {
    const invalidate = useGoalInvalidate()
    const { data: goals, isLoading } = useQuery({ queryKey: ["goals"], queryFn: fetchGoals })
    const { data: breakdown } = useQuery({
        queryKey: ["net-worth-breakdown"],
        queryFn: fetchBreakdown,
    })

    const allSources: Source[] = useMemo(
        () =>
            Object.entries(breakdown?.breakdown ?? {})
                .filter(([, v]) => v !== 0)
                .map(([key, value]) => ({ key, value }))
                .sort((a, b) => b.value - a.value),
        [breakdown],
    )

    // Create form
    const [name, setName] = useState("")
    const [target, setTarget] = useState("")
    const [targetDate, setTargetDate] = useState("")
    const [ringFenced, setRingFenced] = useState(false)
    const [notes, setNotes] = useState("")
    const [formError, setFormError] = useState<string | null>(null)

    const createMut = useMutation({
        mutationFn: () =>
            createGoal({
                name: name.trim(),
                target_amount: target,
                target_date: targetDate || null,
                ring_fenced: ringFenced,
                notes: notes.trim() || null,
            }),
        onSuccess: () => {
            setName("")
            setTarget("")
            setTargetDate("")
            setRingFenced(false)
            setNotes("")
            setFormError(null)
            invalidate()
        },
        onError: (e: Error) => setFormError(e.message),
    })

    const submit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!name.trim() || !Number(target)) {
            setFormError("Give the goal a name and a target amount above zero.")
            return
        }
        createMut.mutate()
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-semibold tracking-tight">Goals</h1>
                <p className="text-sm text-muted-foreground">
                    Save toward a target by earmarking real sources — a trip, a house deposit, an
                    emergency fund. Progress and the funding curve come straight from your daily
                    snapshots. Mark a goal <span className="font-medium">ring-fenced</span> to carve
                    its money out of your Spendable view while keeping it in net worth.
                </p>
            </div>

            {/* New goal */}
            <Card>
                <CardHeader className="border-b">
                    <CardTitle className="text-base">New goal</CardTitle>
                </CardHeader>
                <CardContent>
                    <form className="space-y-4" onSubmit={submit}>
                        <div className="flex flex-wrap items-end gap-3">
                            <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                                Name
                                <Input
                                    className="w-56 rounded-lg border border-input px-3"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="Asia + Australia 2027"
                                />
                            </label>
                            <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                                Target (£)
                                <Input
                                    className="w-36 rounded-lg border border-input px-3"
                                    type="number"
                                    step="any"
                                    value={target}
                                    onChange={(e) => setTarget(e.target.value)}
                                    placeholder="22000"
                                />
                            </label>
                            <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                                Target date (optional)
                                <Input
                                    className="w-44 rounded-lg border border-input px-3"
                                    type="date"
                                    value={targetDate}
                                    onChange={(e) => setTargetDate(e.target.value)}
                                />
                            </label>
                        </div>
                        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                            Notes (optional)
                            <Input
                                className="w-full max-w-lg rounded-lg border border-input px-3"
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                placeholder="Flights, campervan, visas…"
                            />
                        </label>
                        <label className="flex items-center gap-2 text-xs text-muted-foreground">
                            <input
                                type="checkbox"
                                className="size-4 rounded border-input"
                                checked={ringFenced}
                                onChange={(e) => setRingFenced(e.target.checked)}
                            />
                            Ring-fenced — carve this money out of the Spendable view (e.g. a
                            proof-of-funds floor you mustn&apos;t spend)
                        </label>
                        <div className="flex items-center gap-3">
                            <Button type="submit" disabled={createMut.isPending}>
                                <TargetIcon /> {createMut.isPending ? "Creating…" : "Create goal"}
                            </Button>
                            {formError && <span className="text-sm text-destructive">{formError}</span>}
                        </div>
                    </form>
                </CardContent>
            </Card>

            {/* Goal list */}
            {isLoading && <p className="text-muted-foreground">Loading…</p>}
            {goals && goals.length === 0 && (
                <p className="text-sm text-muted-foreground">
                    No goals yet. Create one above to start tracking.
                </p>
            )}
            <div className="grid gap-6 xl:grid-cols-2">
                {goals?.map((g) => (
                    <GoalCard key={g.id} summary={g} allSources={allSources} />
                ))}
            </div>
        </div>
    )
}
