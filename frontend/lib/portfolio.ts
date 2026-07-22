export type Cash = {
    free: number
    invested: number
    ppl: number
    result: number
    total: number
    pieCash: number
    blocked: number | null
}

export type Position = {
    ticker: string
    quantity: number
    currentPrice: number
    averagePrice: number
    ppl: number
}

export type Summary = {
    cash: Cash
    positions: Position[]
    positions_value: number
}

export type SnapshotPoint = {
    date: string
    net_worth: number | null
    total_assets: number | null
}

export async function fetchT212Summary(): Promise<Summary> {
    // /summary is unauthenticated in Phase 0 (see routers/trading212.py), so no token needed yet.
    const res = await fetch("http://localhost:8000/api/integrations/trading212/summary")
    if (!res.ok) throw new Error("Failed to fetch Trading212 summary")
    return res.json()
}

export async function fetchNetWorthSeries(): Promise<SnapshotPoint[]> {
    const res = await fetch("http://localhost:8000/api/net-worth/")
    if (!res.ok) throw new Error("Failed to fetch net-worth history")
    return res.json()
}

export type Breakdown = {
    date: string | null
    net_worth: number | null
    spendable: number
    long_term_keys: string[]
    breakdown: Record<string, number>
}

export async function fetchBreakdown(): Promise<Breakdown> {
    const res = await fetch("http://localhost:8000/api/net-worth/breakdown")
    if (!res.ok) throw new Error("Failed to fetch net-worth breakdown")
    return res.json()
}

// Re-polls every connected source and records today's snapshot, returning the
// fresh breakdown. Used by "Sync now" so newly added/fixed sources show at once.
export async function recordSnapshot(): Promise<Breakdown> {
    const res = await fetch("http://localhost:8000/api/net-worth/snapshot", { method: "POST" })
    if (!res.ok) throw new Error("Failed to record snapshot")
    return res.json()
}

export type Account = {
    id: number
    name: string
    account_type: string
    currency: string
    institution: string | null
    balance: string
    is_active: boolean
    is_long_term: boolean
    monthly_contribution: string
    annual_charge: string
    growth_rate: string
}

export type AccountInput = {
    name: string
    account_type: string
    institution?: string | null
    balance: string
    is_active?: boolean
    is_long_term?: boolean
    monthly_contribution?: string
    annual_charge?: string
    growth_rate?: string
}

const ACCOUNTS_URL = "http://localhost:8000/api/accounts/"

export async function fetchAccounts(): Promise<Account[]> {
    const res = await fetch(ACCOUNTS_URL)
    if (!res.ok) throw new Error("Failed to fetch accounts")
    return res.json()
}

export async function createAccount(input: AccountInput): Promise<Account> {
    const res = await fetch(ACCOUNTS_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
    })
    if (!res.ok) throw new Error("Failed to create account")
    return res.json()
}

export async function updateAccount(id: number, patch: Partial<AccountInput>): Promise<Account> {
    const res = await fetch(`http://localhost:8000/api/accounts/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
    })
    if (!res.ok) throw new Error("Failed to update account")
    return res.json()
}

export async function deleteAccount(id: number): Promise<void> {
    const res = await fetch(`http://localhost:8000/api/accounts/${id}`, { method: "DELETE" })
    if (!res.ok) throw new Error("Failed to delete account")
}

export type ProjectionPoint = {
    date: string
    value: number
    breakdown: Record<string, number>
}

export type Projection = {
    years: number
    series: ProjectionPoint[]
    contributed: number
    growth: number
}

export async function fetchProjection(years: number): Promise<Projection> {
    const res = await fetch(`http://localhost:8000/api/net-worth/projection?years=${years}`)
    if (!res.ok) throw new Error("Failed to fetch projection")
    return res.json()
}

// --- Connections ("bring your own source") ---------------------------------

export type ProviderField = {
    name: string
    label: string
    secret: boolean
    required: boolean
    help: string
    placeholder: string
}

export type Provider = {
    key: string
    display_name: string
    fields: ProviderField[]
    projection_fields: ProviderField[]
}

export type Connection = {
    id: number
    provider: string
    label: string
    is_active: boolean
    is_long_term: boolean
    // Redacted: secret values are absent; `_secrets` marks which are set.
    config: Record<string, unknown> & { _secrets?: Record<string, boolean> }
    // Sync health from the last snapshot.
    last_synced_at: string | null
    last_status: string | null
    last_error: string | null
    last_value: number | null
}

export type ConnectionInput = {
    provider: string
    label: string
    config: Record<string, unknown>
    is_active?: boolean
    is_long_term?: boolean
}

export type ConnectionTestResult = { ok: boolean; value: number | null; error: string | null }

const CONNECTIONS_URL = "http://localhost:8000/api/connections/"

export async function fetchProviders(): Promise<Provider[]> {
    const res = await fetch(`${CONNECTIONS_URL}providers`)
    if (!res.ok) throw new Error("Failed to fetch providers")
    return res.json()
}

export async function fetchConnections(): Promise<Connection[]> {
    const res = await fetch(CONNECTIONS_URL)
    if (!res.ok) throw new Error("Failed to fetch connections")
    return res.json()
}

export async function createConnection(input: ConnectionInput): Promise<Connection> {
    const res = await fetch(CONNECTIONS_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
    })
    if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail ?? "Failed to create connection")
    return res.json()
}

export async function updateConnection(
    id: number,
    patch: Partial<ConnectionInput>,
): Promise<Connection> {
    const res = await fetch(`${CONNECTIONS_URL}${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
    })
    if (!res.ok) throw new Error("Failed to update connection")
    return res.json()
}

export async function deleteConnection(id: number): Promise<void> {
    const res = await fetch(`${CONNECTIONS_URL}${id}`, { method: "DELETE" })
    if (!res.ok) throw new Error("Failed to delete connection")
}

export async function testConnection(
    provider: string,
    config: Record<string, unknown>,
): Promise<ConnectionTestResult> {
    const res = await fetch(`${CONNECTIONS_URL}test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, config }),
    })
    if (!res.ok) throw new Error("Failed to test connection")
    return res.json()
}

// Fetches the full data export and triggers a browser download of the file.
export async function downloadExport(format: "json" | "csv" = "json"): Promise<void> {
    const res = await fetch(`http://localhost:8000/api/export/?format=${format}`)
    if (!res.ok) throw new Error("Failed to export data")

    const blob = await res.blob()
    const stamp = new Date().toISOString().slice(0, 10)
    const ext = format === "csv" ? "zip" : "json"
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `finka-export-${stamp}.${ext}`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
}

// Friendly labels for breakdown keys ("trading212", "account:Tembo", ...).
const SOURCE_LABELS: Record<string, string> = {
    trading212: "Trading212",
    coinbase: "Coinbase",
    monzo: "Monzo",
}

export function sourceLabel(key: string): string {
    // Connection sources carry a user-chosen, already-human-readable label.
    if (key.startsWith("conn:")) return key.slice("conn:".length)
    if (key.startsWith("account:")) return key.slice("account:".length)
    // Fallback for any legacy snapshot keys written before connections existed.
    return SOURCE_LABELS[key] ?? key
}

export const gbp = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" })

export const gbpCompact = new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    notation: "compact",
    maximumFractionDigits: 1,
})

export const pct = new Intl.NumberFormat("en-GB", {
    style: "percent",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
})
