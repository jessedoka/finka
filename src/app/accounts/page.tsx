import { Button } from "../../components/ui/button"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "../../components/ui/dropdown-menu"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "../../components/ui/table"
import React from "react"
import Navigation  from "../../components/Navigation"
import Sidebar from "../../components/Sidebar"

export default function Account() {
    return (
        <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-6">
            <div className="flex items-center">
                <h1 className="font-semibold text-lg md:text-2xl">Accounts</h1>
                <Button className="ml-auto" size="sm">
                    Add Account
                </Button>
            </div>
            <div className="border shadow-sm rounded-lg">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[80px]">Image</TableHead>
                            <TableHead className="max-w-[150px]">Name</TableHead>
                            <TableHead className="hidden md:table-cell">Status</TableHead>
                            <TableHead className="hidden md:table-cell">Inventory</TableHead>
                            <TableHead>Vendor</TableHead>
                            <TableHead className="w-[100px]">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        <TableRow>
                            <TableCell>
                                <img
                                    src="/placeholder.svg"
                                    width="64"
                                    height="64"
                                    alt="Product image"
                                    className="aspect-square rounded-md object-cover"
                                />
                            </TableCell>
                            <TableCell className="font-medium">Glimmer Lamps</TableCell>
                            <TableCell className="hidden md:table-cell">In Production</TableCell>
                            <TableCell>500 in stock</TableCell>
                            <TableCell className="hidden md:table-cell">Luminance Creations</TableCell>
                            <TableCell>
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button aria-haspopup="true" size="icon" variant="ghost">
                                            <div className="h-4 w-4" />
                                            <span className="sr-only">Toggle menu</span>
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end">
                                        <DropdownMenuItem>View</DropdownMenuItem>
                                        <DropdownMenuItem>Edit</DropdownMenuItem>
                                        <DropdownMenuItem>Delete</DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>
                                <img
                                    src="/placeholder.svg"
                                    width="64"
                                    height="64"
                                    alt="Product image"
                                    className="aspect-square rounded-md object-cover"
                                />
                            </TableCell>
                            <TableCell className="font-medium">Aqua Filters</TableCell>
                            <TableCell className="hidden md:table-cell">Available for Order</TableCell>
                            <TableCell>750 in stock</TableCell>
                            <TableCell className="hidden md:table-cell">HydraClean Solutions</TableCell>
                            <TableCell>
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button aria-haspopup="true" size="icon" variant="ghost">
                                            <div className="h-4 w-4" />
                                            <span className="sr-only">Toggle menu</span>
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end">
                                        <DropdownMenuItem>View</DropdownMenuItem>
                                        <DropdownMenuItem>Edit</DropdownMenuItem>
                                        <DropdownMenuItem>Delete</DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>
                                <img
                                    src="/placeholder.svg"
                                    width="64"
                                    height="64"
                                    alt="Product image"
                                    className="aspect-square rounded-md object-cover"
                                />
                            </TableCell>
                            <TableCell className="font-medium">Eco Planters</TableCell>
                            <TableCell className="hidden md:table-cell">Backordered</TableCell>
                            <TableCell>300 in stock</TableCell>
                            <TableCell className="hidden md:table-cell">GreenGrowth Designers</TableCell>
                            <TableCell>
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button aria-haspopup="true" size="icon" variant="ghost">
                                            <div className="h-4 w-4" />
                                            <span className="sr-only">Toggle menu</span>
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end">
                                        <DropdownMenuItem>View</DropdownMenuItem>
                                        <DropdownMenuItem>Edit</DropdownMenuItem>
                                        <DropdownMenuItem>Delete</DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>
                                <img
                                    src="/placeholder.svg"
                                    width="64"
                                    height="64"
                                    alt="Product image"
                                    className="aspect-square rounded-md object-cover"
                                />
                            </TableCell>
                            <TableCell className="font-medium">Zest Juicers</TableCell>
                            <TableCell className="hidden md:table-cell">Newly Launched</TableCell>
                            <TableCell>1000 in stock</TableCell>
                            <TableCell className="hidden md:table-cell">FreshTech Appliances</TableCell>
                            <TableCell>
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button aria-haspopup="true" size="icon" variant="ghost">
                                            <div className="h-4 w-4" />
                                            <span className="sr-only">Toggle menu</span>
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end">
                                        <DropdownMenuItem>View</DropdownMenuItem>
                                        <DropdownMenuItem>Edit</DropdownMenuItem>
                                        <DropdownMenuItem>Delete</DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>
                                <img
                                    src="/placeholder.svg"
                                    width="64"
                                    height="64"
                                    alt="Product image"
                                    className="aspect-square rounded-md object-cover"
                                />
                            </TableCell>
                            <TableCell className="font-medium">Flexi Wearables</TableCell>
                            <TableCell className="hidden md:table-cell">Selling Fast</TableCell>
                            <TableCell>200 in stock</TableCell>
                            <TableCell className="hidden md:table-cell">Vitality Gear Co.</TableCell>
                            <TableCell>
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button aria-haspopup="true" size="icon" variant="ghost">
                                            <div className="h-4 w-4" />
                                            <span className="sr-only">Toggle menu</span>
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end">
                                        <DropdownMenuItem>View</DropdownMenuItem>
                                        <DropdownMenuItem>Edit</DropdownMenuItem>
                                        <DropdownMenuItem>Delete</DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
            </div>
        </main>
    )
}

