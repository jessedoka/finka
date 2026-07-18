"use client"

import { useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { TrendingDownIcon, TrendingUpIcon } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { PortfolioChart } from "@/components/portfolio-chart"
import {
    fetchBreakdown,
    fetchNetWorthSeries,
    gbp,
    pct,
    type SnapshotPoint,
} from "@/lib/portfolio"

const RANGES = [
    { label: "7D", days: 7 },
    { label: "1M", days: 30 },
    { label: "3M", days: 90 },
    { label: "ALL", days: Infinity },
] as const

function seriesForRange(series: SnapshotPoint[], days: number) {
    const points = series
        .filter((p): p is SnapshotPoint & { net_worth: number } => p.net_worth !== null)
        .map((p) => ({ date: p.date, value: p.net_worth }))
    if (days === Infinity) return points
    return points.slice(-days)
}

export function PortfolioOverview() {
    const [range, setRange] = useState<(typeof RANGES)[number]["label"]>("1M")

    const history = useQuery({ queryKey: ["net-worth-series"], queryFn: fetchNetWorthSeries })
    const breakdown = useQuery({ queryKey: ["net-worth-breakdown"], queryFn: fetchBreakdown })

    const activeRange = RANGES.find((r) => r.label === range)!
    const allPoints = useMemo(
        () => seriesForRange(history.data ?? [], Infinity),
        [history.data],
    )
    const points = useMemo(
        () => seriesForRange(history.data ?? [], activeRange.days),
        [history.data, activeRange.days],
    )

    // Headline is the LIVE net worth (snapshot providers + current manual
    // accounts), so an account you just edited shows up immediately; the chart
    // and change badge come from the historical snapshot series.
    const total =
        breakdown.data?.net_worth ?? allPoints[allPoints.length - 1]?.value ?? 0
    const first = points[0]?.value
    const last = points[points.length - 1]?.value
    const change = first !== undefined && last !== undefined ? last - first : 0
    const changePct = first ? change / first : 0
    const positive = change >= 0

    return (
        <Card className="overflow-hidden">
            <CardContent className="space-y-6">
                <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="space-y-2">
                        <p className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                            Net Worth
                        </p>
                        <div className="font-mono text-4xl font-semibold tracking-tight tabular-nums md:text-5xl">
                            {breakdown.isLoading ? (
                                <span className="text-muted-foreground">£—</span>
                            ) : (
                                gbp.format(total)
                            )}
                        </div>
                        {points.length >= 2 && (
                            <div
                                className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-sm font-medium ${
                                    positive
                                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                                        : "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                                }`}
                            >
                                {positive ? (
                                    <TrendingUpIcon className="size-4" />
                                ) : (
                                    <TrendingDownIcon className="size-4" />
                                )}
                                {gbp.format(Math.abs(change))}
                                <span className="opacity-70">
                                    ({positive ? "+" : "−"}
                                    {pct.format(Math.abs(changePct))})
                                </span>
                                <span className="opacity-70">· {range}</span>
                            </div>
                        )}
                    </div>

                    <div className="inline-flex rounded-lg bg-muted p-0.5">
                        {RANGES.map((r) => (
                            <button
                                key={r.label}
                                type="button"
                                onClick={() => setRange(r.label)}
                                className={`rounded-md px-3 py-1.5 text-xs font-semibold tracking-wide transition-colors ${
                                    range === r.label
                                        ? "bg-background text-foreground shadow-sm"
                                        : "text-muted-foreground hover:text-foreground"
                                }`}
                            >
                                {r.label}
                            </button>
                        ))}
                    </div>
                </div>

                {history.isLoading && (
                    <div className="flex h-56 items-center justify-center text-sm text-muted-foreground">
                        Loading chart…
                    </div>
                )}
                {history.isError && (
                    <div className="flex h-56 items-center justify-center text-sm text-destructive">
                        Couldn't load history.
                    </div>
                )}
                {!history.isLoading && !history.isError && points.length < 2 && (
                    <div className="flex h-56 items-center justify-center px-6 text-center text-sm text-muted-foreground">
                        Not enough snapshots yet — the chart appears once there are at least two
                        days of history.
                    </div>
                )}
                {points.length >= 2 && <PortfolioChart data={points} positive={positive} />}
            </CardContent>
        </Card>
    )
}
