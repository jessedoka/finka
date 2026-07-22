"use client"

import { useState } from "react"
import { DownloadIcon, LoaderIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { downloadExport } from "@/lib/portfolio"

export function ExportButton() {
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState(false)

    async function handleExport(format: "json" | "csv") {
        setBusy(true)
        setError(false)
        try {
            await downloadExport(format)
        } catch {
            setError(true)
        } finally {
            setBusy(false)
        }
    }

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    disabled={busy}
                >
                    {busy ? (
                        <LoaderIcon className="animate-spin" />
                    ) : (
                        <DownloadIcon />
                    )}
                    {error ? "Export failed — retry" : busy ? "Exporting…" : "Export data"}
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
                <DropdownMenuItem onClick={() => handleExport("json")}>
                    JSON (full data)
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport("csv")}>
                    CSV (spreadsheet, zipped)
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    )
}
