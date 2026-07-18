"use client"

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

export function NetWorthBreakdown() {
    const { data, isLoading, isError } = useQuery({
        queryKey: ["net-worth-breakdown"],
        queryFn: fetchBreakdown,
    })

    const entries = Object.entries(data?.breakdown ?? {})
        .filter(([, v]) => v !== 0)
        .sort((a, b) => b[1] - a[1])
    const total = entries.reduce((sum, [, v]) => sum + v, 0) || 1

    return (
        <Card className="h-full">
            <CardHeader className="flex-row items-center justify-between border-b">
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
            </CardHeader>
            <CardContent className="space-y-5">
                {isLoading && <p className="text-muted-foreground">Loading…</p>}
                {isError && <p className="text-destructive">Couldn't load breakdown.</p>}

                {data && entries.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                        No snapshot yet — connect a source or add an account, then record a snapshot.
                    </p>
                )}

                {data && entries.length > 0 && (
                    <>
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
