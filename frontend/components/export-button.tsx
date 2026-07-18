"use client"

import { useState } from "react"
import { DownloadIcon, LoaderIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { downloadExport } from "@/lib/portfolio"

export function ExportButton() {
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState(false)

    async function handleExport() {
        setBusy(true)
        setError(false)
        try {
            await downloadExport()
        } catch {
            setError(true)
        } finally {
            setBusy(false)
        }
    }

    return (
        <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={handleExport}
            disabled={busy}
        >
            {busy ? (
                <LoaderIcon className="animate-spin" />
            ) : (
                <DownloadIcon />
            )}
            {error ? "Export failed — retry" : busy ? "Exporting…" : "Export data"}
        </Button>
    )
}
