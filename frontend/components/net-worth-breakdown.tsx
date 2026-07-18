"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { fetchBreakdown, gbp, sourceLabel } from "@/lib/portfolio"

const DOT = [
    "bg-sky-500",
    "bg-amber-500",
    "bg-violet-500",
    "bg-emerald-500",
    "bg-rose-500",
    "bg-cyan-500",
]

const TABS = ["All", "Spendable"] as const

export function NetWorthBreakdown() {
    const [tab, setTab] = useState<(typeof TABS)[number]>("All")
    const { data, isLoading, isError } = useQuery({
        queryKey: ["net-worth-breakdown"],
        queryFn: fetchBreakdown,
    })

    const longTerm = new Set(data?.long_term_keys ?? [])
    const spendableView = tab === "Spendable"

    const entries = Object.entries(data?.breakdown ?? {})
        .filter(([k, v]) => v !== 0 && (!spendableView || !longTerm.has(k)))
        .sort((a, b) => b[1] - a[1])
    const total = entries.reduce((sum, [, v]) => sum + v, 0) || 1
    const hasLongTerm = (data?.long_term_keys ?? []).length > 0

    return (
        <Card className="h-full">
            <CardHeader className="gap-3 border-b">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-base">By Source</CardTitle>
                    {data?.date && (
                        <span className="text-xs text-muted-foreground">
                            as of{" "}
                            {new Date(data.date).toLocaleDateString("en-GB", {
                                day: "numeric",
                                month: "short",
                            })}
                        </span>
                    )}
                </div>
                {hasLongTerm && (
                    <div className="inline-flex w-fit rounded-lg bg-muted p-0.5">
                        {TABS.map((t) => (
                            <button
                                key={t}
                                type="button"
                                onClick={() => setTab(t)}
                                className={`rounded-md px-3 py-1 text-xs font-semibold tracking-wide transition-colors ${
                                    tab === t
                                        ? "bg-background text-foreground shadow-sm"
                                        : "text-muted-foreground hover:text-foreground"
                                }`}
                            >
                                {t}
                            </button>
                        ))}
                    </div>
                )}
            </CardHeader>
            <CardContent className="space-y-5">
                {isLoading && <p className="text-muted-foreground">Loading…</p>}
                {isError && <p className="text-destructive">Couldn't load breakdown.</p>}

                {data && entries.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                        {spendableView
                            ? "Nothing spendable — all assets are marked long-term."
                            : "No snapshot yet — connect a source or add an account, then record a snapshot."}
                    </p>
                )}

                {data && entries.length > 0 && (
                    <>
                        <div>
                            <div className="font-mono text-2xl font-semibold tracking-tight tabular-nums">
                                {gbp.format(spendableView ? data.spendable : (data.net_worth ?? total))}
                            </div>
                            <p className="text-xs text-muted-foreground">
                                {spendableView ? "spendable now" : "total net worth"}
                            </p>
                        </div>

                        <div className="space-y-3">
                            {entries.map(([key, value], i) => {
                                const alloc = value / total
                                return (
                                    <div key={key} className="space-y-1.5">
                                        <div className="flex items-center justify-between gap-3">
                                            <div className="flex min-w-0 items-center gap-2.5">
                                                <span
                                                    className={`size-2.5 shrink-0 rounded-full ${DOT[i % DOT.length]}`}
                                                />
                                                <span className="truncate font-medium">
                                                    {sourceLabel(key)}
                                                </span>
                                                {!spendableView && longTerm.has(key) && (
                                                    <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground uppercase">
                                                        Long-term
                                                    </span>
                                                )}
                                                <span className="shrink-0 font-mono text-xs text-muted-foreground tabular-nums">
                                                    {(alloc * 100).toFixed(1)}%
                                                </span>
                                            </div>
                                            <span className="font-mono text-sm tabular-nums">
                                                {gbp.format(value)}
                                            </span>
                                        </div>
                                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                                            <div
                                                className={`h-full rounded-full ${DOT[i % DOT.length]}`}
                                                style={{ width: `${Math.max(alloc * 100, 2)}%` }}
                                            />
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </>
                )}
            </CardContent>
        </Card>
    )
}
