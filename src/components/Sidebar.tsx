import React from "react";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import Link from "next/link";
import { BellIcon, HomeIcon, LineChartIcon, Package2Icon, PackageIcon, UsersIcon } from "lucide-react"



export default function Sidebar() {
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
                    <Link
                        href="#"
                        className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
                        prefetch={false}
                    >
                        <HomeIcon className="h-4 w-4" />
                        Home
                    </Link>
                    <Link
                        href="#"
                        className="flex items-center gap-3 rounded-lg bg-muted px-3 py-2 text-primary transition-all hover:text-primary"
                        prefetch={false}
                    >
                        <PackageIcon className="h-4 w-4" />
                        Accounts
                    </Link>
                    <Link
                        href="#"
                        className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
                        prefetch={false}
                    >
                        <UsersIcon className="h-4 w-4" />
                        Customers
                    </Link>
                    <Link
                        href="#"
                        className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
                        prefetch={false}
                    >
                        <LineChartIcon className="h-4 w-4" />
                        Analytics
                    </Link>
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