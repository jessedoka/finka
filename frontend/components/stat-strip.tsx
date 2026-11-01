"use client"

import { useQuery } from "@tanstack/react-query"
import { fetchT212Summary, gbp } from "@/lib/portfolio"

function Stat({ label, value, tone }: { label: string; value: string; tone?: "up" | "down" }) {
    return (
        <div className="flex items-center gap-2 whitespace-nowrap">
            <span className="text-sm text-muted-foreground">{label}</span>
            <span
                className={`font-mono text-sm font-semibold tabular-nums ${
                    tone === "up"
                        ? "text-positive"
                        : tone === "down"
                          ? "text-negative"
                          : "text-foreground"
                }`}
            >
                {value}
            </span>
        </div>
    )
}

const time = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" })

export function StatStrip() {
    const { data, dataUpdatedAt } = useQuery({ queryKey: ["t212-summary"], queryFn: fetchT212Summary })

    if (!data) return null

    const up = data.cash.ppl >= 0

    return (
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-xl bg-card px-5 py-3 text-sm ring-1 ring-border">
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-semibold text-muted-foreground">
                Trading212
            </span>
            <span
                className="flex items-center gap-1.5 text-xs font-medium text-positive"
                title="Fetched live from Trading212. The By Source panel shows the last daily snapshot, so the two can differ as prices move."
            >
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-positive" />
                Live
                {dataUpdatedAt > 0 && (
                    <span className="font-normal text-muted-foreground">
                        · {time.format(dataUpdatedAt)}
                    </span>
                )}
            </span>
            <Stat label="Value" value={gbp.format(data.cash.total)} />
            <div className="hidden h-4 w-px bg-border sm:block" />
            <Stat label="Invested" value={gbp.format(data.cash.invested)} />
            <div className="hidden h-4 w-px bg-border sm:block" />
            <Stat label="Free" value={gbp.format(data.cash.free)} />
            <div className="hidden h-4 w-px bg-border sm:block" />
            <Stat
                label="P/L"
                value={`${up ? "+" : "−"}${gbp.format(Math.abs(data.cash.ppl))}`}
                tone={up ? "up" : "down"}
            />
            <div className="hidden h-4 w-px bg-border sm:block" />
            <Stat label="Positions" value={String(data.positions.length)} />
        </div>
    )
}
