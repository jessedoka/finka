"use client"

import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { PencilIcon, PlusIcon, Trash2Icon } from "lucide-react"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
    type Account,
    type AccountInput,
    createAccount,
    deleteAccount,
    fetchAccounts,
    gbp,
    updateAccount,
} from "@/lib/portfolio"

const ACCOUNT_TYPES = ["current", "savings", "pension", "investment", "crypto", "other"]

const EMPTY: AccountInput = {
    name: "",
    account_type: "savings",
    institution: "",
    balance: "",
    is_active: true,
}

const selectClass =
    "h-10 rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring"

export default function AccountsPage() {
    const qc = useQueryClient()
    const invalidate = () => {
        qc.invalidateQueries({ queryKey: ["accounts"] })
        qc.invalidateQueries({ queryKey: ["net-worth-breakdown"] })
    }

    const { data, isLoading, isError } = useQuery({
        queryKey: ["accounts"],
        queryFn: fetchAccounts,
    })

    const [form, setForm] = useState<AccountInput>(EMPTY)
    const [editingId, setEditingId] = useState<number | null>(null)
    const [draft, setDraft] = useState<AccountInput>(EMPTY)

    const createMut = useMutation({
        mutationFn: (input: AccountInput) => createAccount(input),
        onSuccess: () => {
            setForm(EMPTY)
            invalidate()
        },
    })
    const updateMut = useMutation({
        mutationFn: ({ id, patch }: { id: number; patch: Partial<AccountInput> }) =>
            updateAccount(id, patch),
        onSuccess: () => {
            setEditingId(null)
            invalidate()
        },
    })
    const deleteMut = useMutation({
        mutationFn: (id: number) => deleteAccount(id),
        onSuccess: invalidate,
    })

    const startEdit = (a: Account) => {
        setEditingId(a.id)
        setDraft({
            name: a.name,
            account_type: a.account_type,
            institution: a.institution ?? "",
            balance: a.balance,
            is_active: a.is_active,
        })
    }

    const total = (data ?? [])
        .filter((a) => a.is_active)
        .reduce((sum, a) => sum + parseFloat(a.balance), 0)

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-semibold tracking-tight">Accounts</h1>
                    <p className="text-sm text-muted-foreground">
                        Manual balances (pension, savings) that feed your net worth. Live-connected
                        providers (Trading212, Monzo, Coinbase) are tracked automatically.
                    </p>
                </div>
                <div className="text-right">
                    <div className="font-mono text-xl font-semibold tabular-nums">
                        {gbp.format(total)}
                    </div>
                    <div className="text-xs text-muted-foreground">active accounts total</div>
                </div>
            </div>

            {/* Add account */}
            <Card>
                <CardHeader className="border-b">
                    <CardTitle className="text-base">Add an account</CardTitle>
                </CardHeader>
                <CardContent>
                    <form
                        className="flex flex-wrap items-end gap-3"
                        onSubmit={(e) => {
                            e.preventDefault()
                            if (!form.name.trim() || form.balance === "") return
                            createMut.mutate(form)
                        }}
                    >
                        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                            Name
                            <Input
                                className="w-44 rounded-lg border border-input px-3"
                                value={form.name}
                                onChange={(e) => setForm({ ...form, name: e.target.value })}
                                placeholder="Tembo House Saving"
                            />
                        </label>
                        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                            Type
                            <select
                                className={selectClass}
                                value={form.account_type}
                                onChange={(e) => setForm({ ...form, account_type: e.target.value })}
                            >
                                {ACCOUNT_TYPES.map((t) => (
                                    <option key={t} value={t}>
                                        {t}
                                    </option>
                                ))}
                            </select>
                        </label>
                        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                            Institution
                            <Input
                                className="w-40 rounded-lg border border-input px-3"
                                value={form.institution ?? ""}
                                onChange={(e) => setForm({ ...form, institution: e.target.value })}
                                placeholder="Tembo"
                            />
                        </label>
                        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                            Balance (£)
                            <Input
                                className="w-32 rounded-lg border border-input px-3 text-right font-mono"
                                type="number"
                                step="0.01"
                                value={form.balance}
                                onChange={(e) => setForm({ ...form, balance: e.target.value })}
                                placeholder="0.00"
                            />
                        </label>
                        <Button type="submit" disabled={createMut.isPending}>
                            <PlusIcon /> {createMut.isPending ? "Adding…" : "Add"}
                        </Button>
                    </form>
                    {createMut.isError && (
                        <p className="mt-2 text-sm text-destructive">Couldn't add the account.</p>
                    )}
                </CardContent>
            </Card>

            {/* Accounts table */}
            <Card>
                <CardContent className="px-0">
                    {isLoading && <p className="px-6 py-6 text-muted-foreground">Loading…</p>}
                    {isError && (
                        <p className="px-6 py-6 text-destructive">Failed to load accounts.</p>
                    )}
                    {data && data.length === 0 && (
                        <p className="px-6 py-6 text-muted-foreground">
                            No accounts yet. Add one above.
                        </p>
                    )}
                    {data && data.length > 0 && (
                        <Table>
                            <TableHeader>
                                <TableRow className="hover:bg-transparent">
                                    <TableHead className="px-6 text-xs tracking-wide uppercase">
                                        Name
                                    </TableHead>
                                    <TableHead className="text-xs tracking-wide uppercase">
                                        Type
                                    </TableHead>
                                    <TableHead className="text-xs tracking-wide uppercase">
                                        Institution
                                    </TableHead>
                                    <TableHead className="text-xs tracking-wide uppercase">
                                        Status
                                    </TableHead>
                                    <TableHead className="text-right text-xs tracking-wide uppercase">
                                        Balance
                                    </TableHead>
                                    <TableHead className="px-6 text-right text-xs tracking-wide uppercase">
                                        Actions
                                    </TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {data.map((a) => {
                                    const editing = editingId === a.id
                                    return (
                                        <TableRow key={a.id} className={a.is_active ? "" : "opacity-50"}>
                                            <TableCell className="px-6 font-medium">
                                                {editing ? (
                                                    <Input
                                                        className="w-40 rounded-lg border border-input px-2"
                                                        value={draft.name}
                                                        onChange={(e) =>
                                                            setDraft({ ...draft, name: e.target.value })
                                                        }
                                                    />
                                                ) : (
                                                    a.name
                                                )}
                                            </TableCell>
                                            <TableCell className="text-muted-foreground">
                                                {editing ? (
                                                    <select
                                                        className={selectClass}
                                                        value={draft.account_type}
                                                        onChange={(e) =>
                                                            setDraft({
                                                                ...draft,
                                                                account_type: e.target.value,
                                                            })
                                                        }
                                                    >
                                                        {ACCOUNT_TYPES.map((t) => (
                                                            <option key={t} value={t}>
                                                                {t}
                                                            </option>
                                                        ))}
                                                    </select>
                                                ) : (
                                                    a.account_type
                                                )}
                                            </TableCell>
                                            <TableCell className="text-muted-foreground">
                                                {editing ? (
                                                    <Input
                                                        className="w-36 rounded-lg border border-input px-2"
                                                        value={draft.institution ?? ""}
                                                        onChange={(e) =>
                                                            setDraft({
                                                                ...draft,
                                                                institution: e.target.value,
                                                            })
                                                        }
                                                    />
                                                ) : (
                                                    a.institution ?? "—"
                                                )}
                                            </TableCell>
                                            <TableCell>
                                                <button
                                                    type="button"
                                                    onClick={() =>
                                                        updateMut.mutate({
                                                            id: a.id,
                                                            patch: { is_active: !a.is_active },
                                                        })
                                                    }
                                                    className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                                                        a.is_active
                                                            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                                                            : "bg-muted text-muted-foreground"
                                                    }`}
                                                >
                                                    {a.is_active ? "Active" : "Inactive"}
                                                </button>
                                            </TableCell>
                                            <TableCell className="text-right font-mono tabular-nums">
                                                {editing ? (
                                                    <Input
                                                        className="w-28 rounded-lg border border-input px-2 text-right font-mono"
                                                        type="number"
                                                        step="0.01"
                                                        value={draft.balance}
                                                        onChange={(e) =>
                                                            setDraft({ ...draft, balance: e.target.value })
                                                        }
                                                    />
                                                ) : (
                                                    gbp.format(parseFloat(a.balance))
                                                )}
                                            </TableCell>
                                            <TableCell className="px-6">
                                                <div className="flex justify-end gap-1">
                                                    {editing ? (
                                                        <>
                                                            <Button
                                                                size="xs"
                                                                onClick={() =>
                                                                    updateMut.mutate({
                                                                        id: a.id,
                                                                        patch: draft,
                                                                    })
                                                                }
                                                                disabled={updateMut.isPending}
                                                            >
                                                                Save
                                                            </Button>
                                                            <Button
                                                                size="xs"
                                                                variant="ghost"
                                                                onClick={() => setEditingId(null)}
                                                            >
                                                                Cancel
                                                            </Button>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Button
                                                                size="icon-xs"
                                                                variant="ghost"
                                                                onClick={() => startEdit(a)}
                                                                aria-label="Edit"
                                                            >
                                                                <PencilIcon />
                                                            </Button>
                                                            <Button
                                                                size="icon-xs"
                                                                variant="ghost"
                                                                onClick={() => {
                                                                    if (
                                                                        confirm(
                                                                            `Delete "${a.name}"? This can't be undone.`,
                                                                        )
                                                                    )
                                                                        deleteMut.mutate(a.id)
                                                                }}
                                                                aria-label="Delete"
                                                            >
                                                                <Trash2Icon />
                                                            </Button>
                                                        </>
                                                    )}
                                                </div>
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
    )
}
