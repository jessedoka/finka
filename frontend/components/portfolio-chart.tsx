"use client"

import { useId, useState } from "react"
import { gbp } from "@/lib/portfolio"

// SVG viewBox space; the element itself scales to its container width.
const W = 640
const H = 220
const PAD_X = 8
const PAD_Y = 16

type Point = { date: string; value: number }

function buildPath(points: readonly { x: number; y: number }[]): {
    line: string
    area: string
} {
    if (points.length === 0) return { line: "", area: "" }
    const line = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ")
    const area = `${line} L${points[points.length - 1].x},${H - PAD_Y} L${points[0].x},${H - PAD_Y} Z`
    return { line, area }
}

export function PortfolioChart({
    data,
    positive,
}: {
    data: Point[]
    positive: boolean
}) {
    const gradientId = useId()
    const [hover, setHover] = useState<number | null>(null)

    const values = data.map((d) => d.value)
    const min = Math.min(...values)
    const max = Math.max(...values)
    const span = max - min || 1

    const stepX = data.length > 1 ? (W - PAD_X * 2) / (data.length - 1) : 0
    const points = data.map((d, i) => ({
        x: PAD_X + i * stepX,
        y: H - PAD_Y - ((d.value - min) / span) * (H - PAD_Y * 2),
        ...d,
    }))

    const { line, area } = buildPath(points)
    const stroke = positive ? "text-emerald-500" : "text-rose-500"
    const active = hover !== null ? points[hover] : null

    return (
        <div className="relative">
            <svg
                viewBox={`0 0 ${W} ${H}`}
                className={`h-56 w-full ${stroke}`}
                preserveAspectRatio="none"
                role="img"
                aria-label="Portfolio value over time"
            >
                <defs>
                    <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="currentColor" stopOpacity={0.22} />
                        <stop offset="100%" stopColor="currentColor" stopOpacity={0} />
                    </linearGradient>
                </defs>

                {/* subtle horizontal gridlines */}
                {[0.25, 0.5, 0.75].map((t) => (
                    <line
                        key={t}
                        x1={0}
                        x2={W}
                        y1={PAD_Y + t * (H - PAD_Y * 2)}
                        y2={PAD_Y + t * (H - PAD_Y * 2)}
                        className="text-border"
                        stroke="currentColor"
                        strokeWidth={1}
                        strokeDasharray="3 5"
                        vectorEffect="non-scaling-stroke"
                    />
                ))}

                <path d={area} fill={`url(#${gradientId})`} />
                <path
                    d={line}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2}
                    strokeLinejoin="round"
                    strokeLinecap="round"
                    vectorEffect="non-scaling-stroke"
                />

                {active && (
                    <>
                        <line
                            x1={active.x}
                            x2={active.x}
                            y1={0}
                            y2={H}
                            className="text-muted-foreground/50"
                            stroke="currentColor"
                            strokeWidth={1}
                            strokeDasharray="3 4"
                            vectorEffect="non-scaling-stroke"
                        />
                        <circle cx={active.x} cy={active.y} r={4} fill="currentColor" />
                        <circle
                            cx={active.x}
                            cy={active.y}
                            r={8}
                            fill="currentColor"
                            fillOpacity={0.15}
                        />
                    </>
                )}

                {/* invisible hit targets */}
                {points.map((p, i) => (
                    <rect
                        // Index-scoped: a goal-outflow date appears twice (peak + trough
                        // point) to render the dip as a vertical step, so date alone collides.
                        key={`${p.date}-${i}`}
                        x={p.x - stepX / 2}
                        y={0}
                        width={stepX || W}
                        height={H}
                        fill="transparent"
                        onMouseEnter={() => setHover(i)}
                        onMouseLeave={() => setHover(null)}
                    />
                ))}
            </svg>

            {active && (
                <div
                    className="pointer-events-none absolute top-2 z-10 -translate-x-1/2 whitespace-nowrap rounded-lg bg-popover px-3 py-2 text-xs shadow-md ring-1 ring-foreground/10"
                    style={{ left: `${(active.x / W) * 100}%` }}
                >
                    <div className="font-mono text-sm font-semibold text-foreground">
                        {gbp.format(active.value)}
                    </div>
                    <div className="text-muted-foreground">
                        {new Date(active.date).toLocaleDateString("en-GB", {
                            day: "numeric",
                            month: "short",
                            year: "numeric",
                        })}
                    </div>
                </div>
            )}
        </div>
    )
}
