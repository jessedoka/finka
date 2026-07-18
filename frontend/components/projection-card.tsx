"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardContent } from "@/components/ui/card"
import { PortfolioChart } from "@/components/portfolio-chart"
import { fetchProjection, gbp } from "@/lib/portfolio"

const HORIZONS = [5, 10, 20, 30] as const

export function ProjectionCard() {
    const [years, setYears] = useState<number>(10)

    const { data, isLoading, isError } = useQuery({
        queryKey: ["projection", years],
        queryFn: () => fetchProjection(years),
    })

    const points = (data?.series ?? []).map((p) => ({ date: p.date, value: p.value }))
    const projected = points[points.length - 1]?.value ?? 0

    return (
        <Card className="overflow-hidden">
            <CardContent className="space-y-6">
                <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="space-y-2">
                        <p className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                            Projected in {years} years
                        </p>
                        <div className="font-mono text-4xl font-semibold tracking-tight tabular-nums md:text-5xl">
                            {isLoading ? (
                                <span className="text-muted-foreground">£—</span>
                            ) : (
                                gbp.format(projected)
                            )}
                        </div>
                        {data && (
                            <p className="text-sm text-muted-foreground">
                                <span className="text-emerald-600 dark:text-emerald-400">
                                    +{gbp.format(data.contributed)}
                                </span>{" "}
                                contributed ·{" "}
                                <span className="text-sky-600 dark:text-sky-400">
                                    +{gbp.format(data.growth)}
                                </span>{" "}
                                growth
                            </p>
                        )}
                    </div>

                    <div className="inline-flex rounded-lg bg-muted p-0.5">
                        {HORIZONS.map((y) => (
                            <button
                                key={y}
                                type="button"
                                onClick={() => setYears(y)}
                                className={`rounded-md px-3 py-1.5 text-xs font-semibold tracking-wide transition-colors ${
                                    years === y
                                        ? "bg-background text-foreground shadow-sm"
                                        : "text-muted-foreground hover:text-foreground"
                                }`}
                            >
                                {y}Y
                            </button>
                        ))}
                    </div>
                </div>

                {isLoading && (
                    <div className="flex h-56 items-center justify-center text-sm text-muted-foreground">
                        Loading projection…
                    </div>
                )}
                {isError && (
                    <div className="flex h-56 items-center justify-center text-sm text-destructive">
                        Couldn't load projection.
                    </div>
                )}
                {points.length >= 2 && <PortfolioChart data={points} positive />}
            </CardContent>
        </Card>
    )
}
