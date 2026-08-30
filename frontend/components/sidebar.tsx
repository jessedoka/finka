"use client"

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { HomeIcon, Package2Icon, PackageIcon, PlugIcon, TargetIcon } from "lucide-react"
import { ExportButton } from "@/components/export-button"
import { ThemeToggle, Theme } from "@/components/theme-toggle"
import { Button } from "@/components/ui/button"
import { useTheme } from "next-themes"

const menu = [
    {
        title: "Dashboard",
        icon: HomeIcon,
        href: "/dashboard",
    },
    {
        title: "Connections",
        icon: PlugIcon,
        href: "/connections",
    },
    {
        title: "Manual Accounts",
        icon: PackageIcon,
        href: "/accounts",
    },
    {
        title: "Goals",
        icon: TargetIcon,
        href: "/goals",
    }
]


export default function Sidebar() {
    const pathname = usePathname();
    const { theme, setTheme } = useTheme();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    return (
        <div className="flex h-full max-h-screen flex-col gap-2">
            <div className="flex h-15 items-center border-b px-6 justify-between">
                <Link href="/dashboard" className="flex items-center gap-2 font-semibold" prefetch={false}>
                    <Package2Icon className="h-6 w-6" />
                    <span className="">Finka</span>
                </Link>
                {mounted ? (
                    <ThemeToggle theme={theme as Theme} onSelect={setTheme} />
                ) : (
                    <Button variant="outline" size="icon" aria-label="Toggle theme" disabled />
                )}
            </div>
            <div className="flex-1 overflow-auto py-2">
                <nav className="grid items-start px-4 text-sm font-medium">
                    {menu.map((item) => (
                        <Link key={item.title
                        } href={item.href} className={`flex items-center gap-2 p-2 rounded-lg hover:bg-secondary ${pathname === item.href ? "bg-secondary" : ""}`}>
                            <item.icon className="w-6 h-6" />
                            <span>{item.title}</span>
                        </Link>
                    ))}
                </nav>
            </div>
            <div className="border-t p-4 flex items-center gap-2">
                <ExportButton />
            </div>
        </div>
    )
}