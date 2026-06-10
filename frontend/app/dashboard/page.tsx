"use client"

import { useContext, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import { AuthContext } from "@/context/auth"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"

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

async function fetchTransactions(token: string): Promise<Transaction[]> {
    const res = await fetch("http://localhost:8000/api/transactions/", {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    })
    if (!res.ok) throw new Error("Failed to fetch transactions")
    return res.json()
}

export default function DashboardPage() {
    const { token } = useContext(AuthContext)
    const router = useRouter()

    useEffect(() => {
        if (!token) router.push("/login")
    }, [token, router])

    const { data, isLoading, isError } = useQuery({
        queryKey: ["transactions"],
        queryFn: () => fetchTransactions(token!),
        enabled: !!token,
    })

    if (!token) return null
    if (isLoading) return <p className="text-muted-foreground">Loading transactions...</p>
    if (isError) return <p className="text-destructive">Failed to load transactions.</p>

    return (
        <div>
            <h1 className="text-2xl font-semibold mb-6">Transactions</h1>
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead>Merchant</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data?.map((tx) => (
                        <TableRow key={tx.id}>
                            <TableCell>{tx.transaction_date}</TableCell>
                            <TableCell>{tx.description}</TableCell>
                            <TableCell>{tx.merchant_name ?? "—"}</TableCell>
                            <TableCell>{tx.category_name ?? "—"}</TableCell>
                            <TableCell className="text-right font-mono">
                                {parseFloat(tx.amount).toFixed(2)}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    )
}
