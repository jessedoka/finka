"use client"

import { useMemo, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { PlugIcon, RefreshCwIcon, Trash2Icon } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
    type Connection,
    type ConnectionTestResult,
    type Provider,
    type ProviderField,
    createConnection,
    deleteConnection,
    fetchConnections,
    fetchProviders,
    recordSnapshot,
    testConnection,
    updateConnection,
} from "@/lib/portfolio"

const selectClass =
    "h-10 rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring"

function percentToFraction(raw: string): string {
    const n = Number(raw)
    return Number.isFinite(n) ? String(n / 100) : raw
}

function fractionToPercent(stored: unknown): string {
    if (stored === undefined || stored === null || stored === "") return ""
    const n = Number(stored)
    return Number.isFinite(n) ? String(n * 100) : String(stored)
}

// The `headers` field on the generic HTTP provider is a JSON object, entered as
// text; everything else is a plain string. Returns the config object to POST.
function buildConfig(fields: ProviderField[], values: Record<string, string>): Record<string, unknown> {
    const config: Record<string, unknown> = {}
    for (const f of fields) {
        const raw = (values[f.name] ?? "").trim()
        if (!raw) continue
        if (f.name === "headers") config[f.name] = JSON.parse(raw) // may throw -> caught by caller
        else if (f.name === "growth_rate") config[f.name] = percentToFraction(raw)
        else config[f.name] = raw
    }
    return config
}

function ProjectionFieldsEditor({
    connection,
    fields,
    saving,
    onSave,
}: {
    connection: Connection
    fields: ProviderField[]
    saving: boolean
    onSave: (config: Record<string, unknown>) => void
}) {
    const [values, setValues] = useState<Record<string, string>>(() =>
        Object.fromEntries(
            fields.map((f) => [
                f.name,
                f.name === "growth_rate"
                    ? fractionToPercent(connection.config[f.name])
                    : String(connection.config[f.name] ?? ""),
            ]),
        ),
    )

    const save = () => {
        const { _secrets, ...rest } = connection.config
        const config: Record<string, unknown> = { ...rest }
        for (const f of fields) {
            const raw = values[f.name]?.trim()
            if (raw) config[f.name] = f.name === "growth_rate" ? percentToFraction(raw) : raw
            else delete config[f.name]
        }
        onSave(config)
    }

    return (
        <div className="mt-2 flex flex-wrap items-end gap-2 border-t pt-2">
            {fields.map((f) => (
                <label key={f.name} className="flex flex-col gap-1 text-[11px] text-muted-foreground">
                    {f.label}
                    <Input
                        className="h-8 w-32 rounded-md border border-input px-2 text-xs"
                        type="number"
                        step="any"
                        value={values[f.name] ?? ""}
                        placeholder={f.placeholder}
                        onChange={(e) => setValues({ ...values, [f.name]: e.target.value })}
                    />
                </label>
            ))}
            <Button size="xs" variant="secondary" disabled={saving} onClick={save}>
                {saving ? "Saving…" : "Save"}
            </Button>
        </div>
    )
}

export default function ConnectionsPage() {
    const qc = useQueryClient()
    const invalidate = () => {
        qc.invalidateQueries({ queryKey: ["connections"] })
        qc.invalidateQueries({ queryKey: ["net-worth-breakdown"] })
        qc.invalidateQueries({ queryKey: ["projection"] })
    }

    const { data: providers } = useQuery({ queryKey: ["providers"], queryFn: fetchProviders })
    const { data: connections, isLoading } = useQuery({
        queryKey: ["connections"],
        queryFn: fetchConnections,
    })

    const [providerKey, setProviderKey] = useState("")
    const [label, setLabel] = useState("")
    const [isLongTerm, setIsLongTerm] = useState(false)
    const [values, setValues] = useState<Record<string, string>>({})
    const [formError, setFormError] = useState<string | null>(null)
    const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null)

    const provider = useMemo(
        () => providers?.find((p) => p.key === providerKey),
        [providers, providerKey],
    )

    const resetForm = () => {
        setLabel("")
        setValues({})
        setIsLongTerm(false)
        setTestResult(null)
        setFormError(null)
    }

    const pickProvider = (key: string) => {
        setProviderKey(key)
        resetForm()
        const p = providers?.find((x) => x.key === key)
        if (p) setLabel(p.display_name)
    }

    const syncMut = useMutation({
        mutationFn: recordSnapshot,
        onSuccess: invalidate,
    })
    const createMut = useMutation({
        mutationFn: createConnection,
        onSuccess: () => {
            setProviderKey("")
            resetForm()
            invalidate()
            // Poll the new source immediately so it shows in the feed + gets health.
            syncMut.mutate()
        },
        onError: (e: Error) => setFormError(e.message),
    })
    const updateMut = useMutation({
        mutationFn: ({ id, patch }: { id: number; patch: Partial<Connection> }) =>
            updateConnection(id, patch),
        onSuccess: invalidate,
    })
    const deleteMut = useMutation({ mutationFn: deleteConnection, onSuccess: invalidate })
    const testMut = useMutation({
        mutationFn: ({ p, config }: { p: string; config: Record<string, unknown> }) =>
            testConnection(p, config),
        onSuccess: setTestResult,
    })

    const assemble = (): Record<string, unknown> | null => {
        if (!provider) return null
        try {
            setFormError(null)
            return buildConfig([...provider.fields, ...provider.projection_fields], values)
        } catch {
            setFormError("Headers must be valid JSON, e.g. {\"Authorization\": \"Bearer …\"}")
            return null
        }
    }

    const submit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!provider || !label.trim()) return
        const config = assemble()
        if (config === null) return
        createMut.mutate({
            provider: provider.key,
            label: label.trim(),
            config,
            is_long_term: isLongTerm,
        })
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-semibold tracking-tight">Connections</h1>
                <p className="text-sm text-muted-foreground">
                    Bring your own data sources. Connect a supported provider or point the generic
                    HTTP connector at any endpoint that returns a JSON balance — Finka polls it into
                    your net worth. Credentials are stored on your instance and never shown again
                    once saved.
                </p>
            </div>

            {/* Add a connection */}
            <Card>
                <CardHeader className="border-b">
                    <CardTitle className="text-base">Add a source</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex flex-wrap items-end gap-3">
                        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                            Provider
                            <select
                                className={selectClass}
                                value={providerKey}
                                onChange={(e) => pickProvider(e.target.value)}
                            >
                                <option value="">Select…</option>
                                {providers?.map((p) => (
                                    <option key={p.key} value={p.key}>
                                        {p.display_name}
                                    </option>
                                ))}
                            </select>
                        </label>
                        {provider && (
                            <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                                Label
                                <Input
                                    className="w-48 rounded-lg border border-input px-3"
                                    value={label}
                                    onChange={(e) => setLabel(e.target.value)}
                                    placeholder="My Monzo pots"
                                />
                            </label>
                        )}
                    </div>

                    {provider && (
                        <form className="space-y-4" onSubmit={submit}>
                            <div className="flex flex-wrap gap-3">
                                {provider.fields.map((f) => (
                                    <label
                                        key={f.name}
                                        className="flex flex-col gap-1 text-xs text-muted-foreground"
                                    >
                                        <span>
                                            {f.label}
                                            {f.required && <span className="text-destructive"> *</span>}
                                        </span>
                                        <Input
                                            className="w-64 rounded-lg border border-input px-3"
                                            type={f.secret ? "password" : "text"}
                                            value={values[f.name] ?? ""}
                                            placeholder={f.placeholder}
                                            onChange={(e) =>
                                                setValues({ ...values, [f.name]: e.target.value })
                                            }
                                        />
                                        {f.help && (
                                            <span className="max-w-64 text-[11px] leading-tight text-muted-foreground/70">
                                                {f.help}
                                            </span>
                                        )}
                                    </label>
                                ))}
                            </div>

                            {provider.projection_fields.length > 0 && (
                                <div className="space-y-2 border-t pt-3">
                                    <p className="text-xs font-medium text-muted-foreground">
                                        Projection (optional) — how this source should compound in the
                                        projection chart. Left blank, it's held flat at today's value.
                                    </p>
                                    <div className="flex flex-wrap gap-3">
                                        {provider.projection_fields.map((f) => (
                                            <label
                                                key={f.name}
                                                className="flex flex-col gap-1 text-xs text-muted-foreground"
                                            >
                                                <span>{f.label}</span>
                                                <Input
                                                    className="w-64 rounded-lg border border-input px-3"
                                                    type="number"
                                                    step="any"
                                                    value={values[f.name] ?? ""}
                                                    placeholder={f.placeholder}
                                                    onChange={(e) =>
                                                        setValues({ ...values, [f.name]: e.target.value })
                                                    }
                                                />
                                                {f.help && (
                                                    <span className="max-w-64 text-[11px] leading-tight text-muted-foreground/70">
                                                        {f.help}
                                                    </span>
                                                )}
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <label className="flex items-center gap-2 text-xs text-muted-foreground">
                                <input
                                    type="checkbox"
                                    className="size-4 rounded border-input"
                                    checked={isLongTerm}
                                    onChange={(e) => setIsLongTerm(e.target.checked)}
                                />
                                Long-term (locked) — excluded from the Spendable view
                            </label>

                            <div className="flex items-center gap-3">
                                <Button type="submit" disabled={createMut.isPending}>
                                    <PlugIcon /> {createMut.isPending ? "Saving…" : "Save connection"}
                                </Button>
                                <Button
                                    type="button"
                                    variant="secondary"
                                    disabled={testMut.isPending}
                                    onClick={() => {
                                        const config = assemble()
                                        if (config !== null)
                                            testMut.mutate({ p: provider.key, config })
                                    }}
                                >
                                    {testMut.isPending ? "Testing…" : "Test"}
                                </Button>
                                {testResult?.ok && (
                                    <span className="text-sm text-emerald-600 dark:text-emerald-400">
                                        ✓ Fetched £{testResult.value?.toLocaleString()}
                                    </span>
                                )}
                                {testResult && !testResult.ok && (
                                    <span className="text-sm text-destructive">✗ {testResult.error}</span>
                                )}
                            </div>
                            {formError && <p className="text-sm text-destructive">{formError}</p>}
                        </form>
                    )}
                </CardContent>
            </Card>

            {/* Existing connections */}
            <Card>
                <CardHeader className="border-b">
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-base">Your sources</CardTitle>
                        <Button
                            size="xs"
                            variant="secondary"
                            disabled={syncMut.isPending}
                            onClick={() => syncMut.mutate()}
                            title="Re-poll every source now and refresh the dashboard"
                        >
                            <RefreshCwIcon className={syncMut.isPending ? "animate-spin" : ""} />
                            {syncMut.isPending ? "Syncing…" : "Sync now"}
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="divide-y p-0">
                    {isLoading && <p className="px-6 py-6 text-muted-foreground">Loading…</p>}
                    {connections && connections.length === 0 && (
                        <p className="px-6 py-6 text-muted-foreground">
                            No sources yet. Add one above.
                        </p>
                    )}
                    {connections?.map((c) => (
                        <div key={c.id} className="flex flex-wrap items-center justify-between gap-4 px-6 py-3">
                            <div className="min-w-0">
                                <div className="font-medium">{c.label}</div>
                                <div className="text-xs text-muted-foreground">
                                    {providers?.find((p) => p.key === c.provider)?.display_name ??
                                        c.provider}
                                </div>
                                {c.last_status === "error" ? (
                                    <div className="mt-0.5 text-xs text-destructive">
                                        ⚠ {c.last_error ?? "Last sync failed"}
                                    </div>
                                ) : c.last_status === "ok" ? (
                                    <div className="mt-0.5 text-xs text-emerald-600 dark:text-emerald-400">
                                        ✓ £{c.last_value?.toLocaleString()} · synced{" "}
                                        {c.last_synced_at
                                            ? new Date(c.last_synced_at).toLocaleString("en-GB", {
                                                  day: "numeric",
                                                  month: "short",
                                                  hour: "2-digit",
                                                  minute: "2-digit",
                                              })
                                            : ""}
                                    </div>
                                ) : (
                                    <div className="mt-0.5 text-xs text-muted-foreground">
                                        Not synced yet — hit “Sync now”.
                                    </div>
                                )}
                            </div>
                            <div className="flex items-center gap-1">
                                <button
                                    type="button"
                                    onClick={() =>
                                        updateMut.mutate({
                                            id: c.id,
                                            patch: { is_long_term: !c.is_long_term },
                                        })
                                    }
                                    className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                                        c.is_long_term
                                            ? "bg-violet-500/10 text-violet-600 dark:text-violet-400"
                                            : "bg-muted text-muted-foreground"
                                    }`}
                                    title="Long-term/locked sources are excluded from the Spendable view"
                                >
                                    {c.is_long_term ? "Long-term" : "Spendable"}
                                </button>
                                <button
                                    type="button"
                                    onClick={() =>
                                        updateMut.mutate({
                                            id: c.id,
                                            patch: { is_active: !c.is_active },
                                        })
                                    }
                                    className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                                        c.is_active
                                            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                                            : "bg-muted text-muted-foreground"
                                    }`}
                                >
                                    {c.is_active ? "Active" : "Inactive"}
                                </button>
                                <Button
                                    size="icon-xs"
                                    variant="ghost"
                                    aria-label="Delete"
                                    onClick={() => {
                                        if (confirm(`Delete "${c.label}"? This can't be undone.`))
                                            deleteMut.mutate(c.id)
                                    }}
                                >
                                    <Trash2Icon />
                                </Button>
                            </div>
                            {(() => {
                                const spec = providers?.find((p) => p.key === c.provider)
                                if (!spec || spec.projection_fields.length === 0) return null
                                return (
                                    <div className="basis-full">
                                        <ProjectionFieldsEditor
                                            connection={c}
                                            fields={spec.projection_fields}
                                            saving={
                                                updateMut.isPending && updateMut.variables?.id === c.id
                                            }
                                            onSave={(config) =>
                                                updateMut.mutate({ id: c.id, patch: { config } })
                                            }
                                        />
                                    </div>
                                )
                            })()}
                        </div>
                    ))}
                </CardContent>
            </Card>
        </div>
    )
}
