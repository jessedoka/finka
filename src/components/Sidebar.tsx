"use client"

import React from "react";
import { Button } from "./ui/button";
import { usePathname } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import Link from "next/link";
import { BellIcon, HomeIcon, LineChartIcon, Package2Icon, PackageIcon, UsersIcon } from "lucide-react"

const menu = [
    {
        title: "Dashboard",
        icon: HomeIcon,
        href: "/",
    },
    {
        title: "Accounts",
        icon: PackageIcon,
        href: "/accounts",
    },
    {
        title: "All Transactions",
        icon: UsersIcon,
        href: "#",
    },
]


export default function Sidebar() {
    const pathname = usePathname();
    
    return (
        <div className="flex h-full max-h-screen flex-col gap-2">
            <div className="flex h-[60px] items-center border-b px-6">
                <Link href="#" className="flex items-center gap-2 font-semibold" prefetch={false}>
                    <Package2Icon className="h-6 w-6" />
                    <span className="">Finka</span>
                </Link>
                <Button variant="outline" size="icon" className="ml-auto h-8 w-8">
                    <BellIcon className="h-4 w-4" />
                    <span className="sr-only">Toggle notifications</span>
                </Button>
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
            <div className="mt-auto p-4">
                <Card>
                    <CardHeader className="pb-4">
                        <CardTitle>Upgrade to Pro</CardTitle>
                        <CardDescription>Unlock all features and get unlimited access to our support team</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Button size="sm" className="w-full">
                            Upgrade
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}