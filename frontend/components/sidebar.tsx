"use client"

import { usePathname } from "next/navigation";
import Link from "next/link";
import { HomeIcon, Package2Icon, PackageIcon, PlugIcon, TargetIcon } from "lucide-react"
import { ExportButton } from "@/components/export-button"

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

    return (
        <div className="flex h-full max-h-screen flex-col gap-2">
            <div className="flex h-15 items-center border-b px-6">
                <Link href="/dashboard" className="flex items-center gap-2 font-semibold" prefetch={false}>
                    <Package2Icon className="h-6 w-6" />
                    <span className="">Finka</span>
                </Link>
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
            <div className="border-t p-4">
                <ExportButton />
            </div>
        </div>
    )
}