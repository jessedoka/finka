"use client"

import { PortfolioOverview } from "@/components/portfolio-overview"
import { PortfolioStats } from "@/components/portfolio-stats"
import { NetWorthBreakdown } from "@/components/net-worth-breakdown"
import { ProjectionCard } from "@/components/projection-card"
import { StatStrip } from "@/components/stat-strip"

export default function DashboardPage() {
    return (
        <div className="space-y-6">
            <StatStrip />

            <div className="grid gap-6 lg:grid-cols-3">
                <div className="lg:col-span-2">
                    <PortfolioOverview />
                </div>
                <div className="lg:col-span-1">
                    <NetWorthBreakdown />
                </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
                <div className="lg:col-span-2">
                    <ProjectionCard />
                </div>
                <div className="lg:col-span-1">
                    <PortfolioStats />
                </div>
            </div>
        </div>
    )
}
