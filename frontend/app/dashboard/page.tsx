"use client"

import { useQuery } from "@tanstack/react-query"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PortfolioOverview } from "@/components/portfolio-overview"
import { PortfolioStats } from "@/components/portfolio-stats"
import { NetWorthBreakdown } from "@/components/net-worth-breakdown"
import { StatStrip } from "@/components/stat-strip"
import { gbp } from "@/lib/portfolio"

const RECENT_LIMIT = 10

type Transaction = {
    id: number
    account_id: number
    amount: string
    description: string
    merchant_name: string | null
    transaction_date: string
    category_id: number | null
    category_name: string | null
}

async function fetchTransactions(): Promise<Transaction[]> {
    // Auth is stubbed in local dev (backend resolves the dev user), so no token is sent.
    const res = await fetch("http://localhost:8000/api/transactions/")
    if (!res.ok) throw new Error("Failed to fetch transactions")
    return res.json()
}

function formatDate(value: string) {
    const d = new Date(value)
    if (Number.isNaN(d.getTime())) return value
    return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })
}

export default function DashboardPage() {
    const { data, isLoading, isError } = useQuery({
        queryKey: ["transactions"],
        queryFn: fetchTransactions,
    })

    const recent = data?.slice(0, RECENT_LIMIT) ?? []

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
                <div className="lg:col-span-1">
                    <PortfolioStats />
                </div>

                <Card className="lg:col-span-2">
                    <CardHeader className="flex-row items-center justify-between border-b">
                        <CardTitle className="text-base">Recent Transactions</CardTitle>
                        {data && data.length > RECENT_LIMIT && (
                            <Link
                                href="#"
                                className="text-xs font-medium text-muted-foreground hover:text-foreground"
                            >
                                {data.length} total
                            </Link>
                        )}
                    </CardHeader>
                    <CardContent className="px-0">
                    {isLoading && (
                        <p className="px-8 py-6 text-muted-foreground">Loading transactions…</p>
                    )}
                    {isError && (
                        <p className="px-8 py-6 text-destructive">Failed to load transactions.</p>
                    )}
                    {data && data.length === 0 && (
                        <p className="px-8 py-6 text-muted-foreground">No transactions yet.</p>
                    )}
                    {data && data.length > 0 && (
                        <Table>
                            <TableHeader>
                                <TableRow className="hover:bg-transparent">
                                    <TableHead className="px-8 text-xs tracking-wide uppercase">
                                        Date
                                    </TableHead>
                                    <TableHead className="text-xs tracking-wide uppercase">
                                        Description
                                    </TableHead>
                                    <TableHead className="text-xs tracking-wide uppercase">
                                        Merchant
                                    </TableHead>
                                    <TableHead className="text-xs tracking-wide uppercase">
                                        Category
                                    </TableHead>
                                    <TableHead className="px-8 text-right text-xs tracking-wide uppercase">
                                        Amount
                                    </TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {recent.map((tx) => {
                                    const amount = parseFloat(tx.amount)
                                    const negative = amount < 0
                                    return (
                                        <TableRow key={tx.id}>
                                            <TableCell className="px-8 whitespace-nowrap text-muted-foreground">
                                                {formatDate(tx.transaction_date)}
                                            </TableCell>
                                            <TableCell className="font-medium">
                                                {tx.description}
                                            </TableCell>
                                            <TableCell className="text-muted-foreground">
                                                {tx.merchant_name ?? "—"}
                                            </TableCell>
                                            <TableCell>
                                                {tx.category_name ? (
                                                    <span className="inline-flex rounded-md bg-muted px-2 py-0.5 text-xs font-medium">
                                                        {tx.category_name}
                                                    </span>
                                                ) : (
                                                    <span className="text-muted-foreground">—</span>
                                                )}
                                            </TableCell>
                                            <TableCell
                                                className={`px-8 text-right font-mono tabular-nums ${
                                                    negative
                                                        ? "text-foreground"
                                                        : "text-emerald-600 dark:text-emerald-400"
                                                }`}
                                            >
                                                {negative ? "" : "+"}
                                                {gbp.format(amount)}
                                            </TableCell>
                                        </TableRow>
                                    )
                                })}
                            </TableBody>
                        </Table>
                    )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
