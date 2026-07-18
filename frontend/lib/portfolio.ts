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
