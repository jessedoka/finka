import { MonitorIcon, MoonIcon, SunIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export type Theme = "light" | "dark" | "system"

const options: { value: Theme; label: string; icon: typeof SunIcon }[] = [
    { value: "light", label: "Light", icon: SunIcon },
    { value: "dark", label: "Dark", icon: MoonIcon },
    { value: "system", label: "System", icon: MonitorIcon },
]

/**
 * Presentational only — pass the current theme and a callback to apply it.
 * Wire this up with next-themes' `useTheme()` where it's rendered.
 */
export function ThemeToggle({
    theme,
    onSelect,
}: {
    theme: Theme
    onSelect: (theme: Theme) => void
}) {
    const Current = options.find((option) => option.value === theme)?.icon ?? SunIcon

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon" aria-label="Toggle theme">
                    <Current />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
                {options.map(({ value, label, icon: Icon }) => (
                    <DropdownMenuItem key={value} onClick={() => onSelect(value)}>
                        <Icon />
                        {label}
                    </DropdownMenuItem>
                ))}
            </DropdownMenuContent>
        </DropdownMenu>
    )
}
