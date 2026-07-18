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
const PROJECT_YEARS = 10

// UI-friendly draft: growth as a percent string (e.g. "5"), converted to a
// fraction ("0.05") at the API boundary.
type Draft = {
    name: string
    account_type: string
    institution: string
    balance: string
    monthly_contribution: string
    annual_charge: string
    growth_pct: string
    is_long_term: boolean
}

const EMPTY: Draft = {
    name: "",
    account_type: "savings",
    institution: "",
    balance: "",
    monthly_contribution: "",
    annual_charge: "",
    growth_pct: "5",
    is_long_term: false,
}

const selectClass =
    "h-10 rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring"

function draftToInput(d: Draft): AccountInput {
    return {
        name: d.name,
        account_type: d.account_type,
        institution: d.institution,
        balance: d.balance === "" ? "0" : d.balance,
        is_long_term: d.is_long_term,
        monthly_contribution: d.monthly_contribution === "" ? "0" : d.monthly_contribution,
        annual_charge: d.annual_charge === "" ? "0" : d.annual_charge,
        growth_rate: ((parseFloat(d.growth_pct) || 0) / 100).toString(),
    }
}

function accountToDraft(a: Account): Draft {
    return {
        name: a.name,
        account_type: a.account_type,
        institution: a.institution ?? "",
        balance: a.balance,
        monthly_contribution: a.monthly_contribution,
        annual_charge: a.annual_charge,
        growth_pct: ((parseFloat(a.growth_rate) || 0) * 100).toString(),
        is_long_term: a.is_long_term,
    }
}

// Same monthly recurrence as the backend, for a single account's projected value.
function projectValue(a: Account, years = PROJECT_YEARS): number {
    let v = parseFloat(a.balance) || 0
    const m = parseFloat(a.monthly_contribution) || 0
    const c = parseFloat(a.annual_charge) || 0
    const g = parseFloat(a.growth_rate) || 0
    for (let i = 0; i < years * 12; i++) v = v * (1 + g / 12) + m - c / 12
    return v
}

export default function AccountsPage() {
    const qc = useQueryClient()
    const invalidate = () => {
        qc.invalidateQueries({ queryKey: ["accounts"] })
        qc.invalidateQueries({ queryKey: ["net-worth-breakdown"] })
        qc.invalidateQueries({ queryKey: ["projection"] })
    }

    const { data, isLoading, isError } = useQuery({
        queryKey: ["accounts"],
        queryFn: fetchAccounts,
    })

    const [form, setForm] = useState<Draft>(EMPTY)
    const [editingId, setEditingId] = useState<number | null>(null)
    const [draft, setDraft] = useState<Draft>(EMPTY)

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

    const total = (data ?? [])
        .filter((a) => a.is_active)
        .reduce((sum, a) => sum + parseFloat(a.balance), 0)

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-semibold tracking-tight">Manual Accounts</h1>
                    <p className="text-sm text-muted-foreground">
                        Balances you keep up to date by hand (pension, savings) that feed your net
                        worth and its projection. Live-connected providers (Trading212, Monzo,
                        Coinbase) are tracked automatically.
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
                            if (!form.name.trim()) return
                            createMut.mutate(draftToInput(form))
                        }}
                    >
                        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                            Name
                            <Input
                                className="w-40 rounded-lg border border-input px-3"
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
                            Balance (£)
                            <Input
                                className="w-28 rounded-lg border border-input px-3 text-right font-mono"
                                type="number"
                                step="0.01"
                                value={form.balance}
                                onChange={(e) => setForm({ ...form, balance: e.target.value })}
                                placeholder="0.00"
                            />
                        </label>
                        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                            Contribution (£/mo)
                            <Input
                                className="w-28 rounded-lg border border-input px-3 text-right font-mono"
                                type="number"
                                step="0.01"
                                value={form.monthly_contribution}
                                onChange={(e) =>
                                    setForm({ ...form, monthly_contribution: e.target.value })
                                }
                                placeholder="0.00"
                            />
                        </label>
                        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                            Growth (%/yr)
                            <Input
                                className="w-24 rounded-lg border border-input px-3 text-right font-mono"
                                type="number"
                                step="0.1"
                                value={form.growth_pct}
                                onChange={(e) => setForm({ ...form, growth_pct: e.target.value })}
                                placeholder="5"
                            />
                        </label>
                        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                            Charge (£/yr)
                            <Input
                                className="w-24 rounded-lg border border-input px-3 text-right font-mono"
                                type="number"
                                step="0.01"
                                value={form.annual_charge}
                                onChange={(e) => setForm({ ...form, annual_charge: e.target.value })}
                                placeholder="0.00"
                            />
                        </label>
                        <label className="flex items-center gap-2 pb-2.5 text-xs text-muted-foreground">
                            <input
                                type="checkbox"
                                className="size-4 rounded border-input"
                                checked={form.is_long_term}
                                onChange={(e) =>
                                    setForm({ ...form, is_long_term: e.target.checked })
                                }
                            />
                            Long-term (locked)
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
                                    <TableHead className="text-right text-xs tracking-wide uppercase">
                                        Balance
                                    </TableHead>
                                    <TableHead className="text-right text-xs tracking-wide uppercase">
                                        £/mo
                                    </TableHead>
                                    <TableHead className="text-right text-xs tracking-wide uppercase">
                                        Growth
                                    </TableHead>
                                    <TableHead className="text-right text-xs tracking-wide uppercase">
                                        Charge
                                    </TableHead>
                                    <TableHead className="text-right text-xs tracking-wide uppercase">
                                        In {PROJECT_YEARS}y
                                    </TableHead>
                                    <TableHead className="text-xs tracking-wide uppercase">
                                        Horizon
                                    </TableHead>
                                    <TableHead className="text-xs tracking-wide uppercase">
                                        Status
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
                                                        className="w-36 rounded-lg border border-input px-2"
                                                        value={draft.name}
                                                        onChange={(e) =>
                                                            setDraft({ ...draft, name: e.target.value })
                                                        }
                                                    />
                                                ) : (
                                                    <>
                                                        {a.name}
                                                        <span className="block text-xs font-normal text-muted-foreground">
                                                            {a.institution ?? a.account_type}
                                                        </span>
                                                    </>
                                                )}
                                            </TableCell>
                                            <TableCell className="text-right font-mono tabular-nums">
                                                {editing ? (
                                                    <Input
                                                        className="w-24 rounded-lg border border-input px-2 text-right font-mono"
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
                                            <TableCell className="text-right font-mono tabular-nums">
                                                {editing ? (
                                                    <Input
                                                        className="w-20 rounded-lg border border-input px-2 text-right font-mono"
                                                        type="number"
                                                        step="0.01"
                                                        value={draft.monthly_contribution}
                                                        onChange={(e) =>
                                                            setDraft({
                                                                ...draft,
                                                                monthly_contribution: e.target.value,
                                                            })
                                                        }
                                                    />
                                                ) : (
                                                    gbp.format(parseFloat(a.monthly_contribution))
                                                )}
                                            </TableCell>
                                            <TableCell className="text-right font-mono tabular-nums text-muted-foreground">
                                                {editing ? (
                                                    <Input
                                                        className="w-16 rounded-lg border border-input px-2 text-right font-mono"
                                                        type="number"
                                                        step="0.1"
                                                        value={draft.growth_pct}
                                                        onChange={(e) =>
                                                            setDraft({
                                                                ...draft,
                                                                growth_pct: e.target.value,
                                                            })
                                                        }
                                                    />
                                                ) : (
                                                    `${(parseFloat(a.growth_rate) * 100).toFixed(1)}%`
                                                )}
                                            </TableCell>
                                            <TableCell className="text-right font-mono tabular-nums text-muted-foreground">
                                                {editing ? (
                                                    <Input
                                                        className="w-20 rounded-lg border border-input px-2 text-right font-mono"
                                                        type="number"
                                                        step="0.01"
                                                        value={draft.annual_charge}
                                                        onChange={(e) =>
                                                            setDraft({
                                                                ...draft,
                                                                annual_charge: e.target.value,
                                                            })
                                                        }
                                                    />
                                                ) : (
                                                    gbp.format(parseFloat(a.annual_charge))
                                                )}
                                            </TableCell>
                                            <TableCell className="text-right font-mono tabular-nums font-medium">
                                                {gbp.format(projectValue(a))}
                                            </TableCell>
                                            <TableCell>
                                                <button
                                                    type="button"
                                                    onClick={() =>
                                                        updateMut.mutate({
                                                            id: a.id,
                                                            patch: { is_long_term: !a.is_long_term },
                                                        })
                                                    }
                                                    className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                                                        a.is_long_term
                                                            ? "bg-violet-500/10 text-violet-600 dark:text-violet-400"
                                                            : "bg-muted text-muted-foreground"
                                                    }`}
                                                    title="Long-term/locked assets are excluded from the Spendable view"
                                                >
                                                    {a.is_long_term ? "Long-term" : "Spendable"}
                                                </button>
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
                                            <TableCell className="px-6">
                                                <div className="flex justify-end gap-1">
                                                    {editing ? (
                                                        <>
                                                            <Button
                                                                size="xs"
                                                                onClick={() =>
                                                                    updateMut.mutate({
                                                                        id: a.id,
                                                                        patch: draftToInput(draft),
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
                                                                onClick={() => {
                                                                    setEditingId(a.id)
                                                                    setDraft(accountToDraft(a))
                                                                }}
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
