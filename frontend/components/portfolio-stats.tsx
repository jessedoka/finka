"use client"

import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { fetchT212Summary, gbp, type Position } from "@/lib/portfolio"

// A small rotating palette so each holding gets a stable-ish accent colour.
const DOT = [
    "bg-sky-500",
    "bg-amber-500",
    "bg-violet-500",
    "bg-emerald-500",
    "bg-rose-500",
    "bg-cyan-500",
]

function positionValue(p: Position) {
    return p.quantity * p.currentPrice
}

export function PortfolioStats() {
    const { data, isLoading, isError } = useQuery({
        queryKey: ["t212-summary"],
        queryFn: fetchT212Summary,
    })

    const positions = [...(data?.positions ?? [])].sort(
        (a, b) => positionValue(b) - positionValue(a),
    )
    const investedTotal = positions.reduce((sum, p) => sum + positionValue(p), 0) || 1

    return (
        <Card className="h-full">
            <CardHeader className="border-b">
                <CardTitle className="text-base">Portfolio Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {isLoading && <p className="text-muted-foreground">Loading…</p>}
                {isError && <p className="text-destructive">Couldn't reach Trading212.</p>}

                {data && positions.length === 0 && (
                    <p className="text-sm text-muted-foreground">No open positions.</p>
                )}

                {data &&
                    positions.slice(0, 6).map((p, i) => {
                        const value = positionValue(p)
                        const alloc = value / investedTotal
                        const up = p.ppl >= 0
                        return (
                            <div key={p.ticker} className="space-y-1.5">
                                <div className="flex items-center justify-between gap-3">
                                    <div className="flex min-w-0 items-center gap-2.5">
                                        <span
                                            className={`size-2.5 shrink-0 rounded-full ${DOT[i % DOT.length]}`}
                                        />
                                        <span className="truncate font-medium">{p.ticker}</span>
                                        <span className="shrink-0 font-mono text-xs text-muted-foreground tabular-nums">
                                            {(alloc * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-mono text-sm tabular-nums">
                                            {gbp.format(value)}
                                        </div>
                                        <div
                                            className={`font-mono text-xs tabular-nums ${
                                                up
                                                    ? "text-emerald-600 dark:text-emerald-400"
                                                    : "text-rose-600 dark:text-rose-400"
                                            }`}
                                        >
                                            {up ? "▲" : "▼"} {gbp.format(Math.abs(p.ppl))}
                                        </div>
                                    </div>
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

                {data && (
                    <dl className="grid grid-cols-2 gap-x-4 gap-y-2 border-t pt-4 text-sm">
                        <dt className="text-muted-foreground">Invested</dt>
                        <dd className="text-right font-mono tabular-nums">
                            {gbp.format(data.cash.invested)}
                        </dd>
                        <dt className="text-muted-foreground">Free cash</dt>
                        <dd className="text-right font-mono tabular-nums">
                            {gbp.format(data.cash.free)}
                        </dd>
                        <dt className="text-muted-foreground">Total P/L</dt>
                        <dd
                            className={`text-right font-mono tabular-nums ${
                                data.cash.ppl >= 0
                                    ? "text-emerald-600 dark:text-emerald-400"
                                    : "text-rose-600 dark:text-rose-400"
                            }`}
                        >
                            {data.cash.ppl >= 0 ? "+" : "−"}
                            {gbp.format(Math.abs(data.cash.ppl))}
                        </dd>
                    </dl>
                )}
            </CardContent>
        </Card>
    )
}
