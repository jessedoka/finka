"use client"

import React, { useState } from "react"
import { Button } from "./ui/button"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "./ui/dropdown-menu"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "./ui/table"
import { useToast } from "./ui/use-toast"
import { useRouter } from "next/navigation"
import { api } from "../trpc/react"

type allAccountProps = { 
    id: number; 
    name: string; 
    createdAt: Date; 
    updatedAt: Date; 
    user_id: string | null; 
}[]

export default function AccountTable({allAccounts}: {allAccounts: allAccountProps}) {
    const [editMode, setEditMode] = useState<Record<number, boolean>>({}); 
    const router = useRouter();
    const { toast } = useToast()

    const toggleEditMode = (accountId: number) => {
        setEditMode((prev) => ({ ...prev, [accountId]: !prev[accountId] }));
    };

    const updateAccount = api.account.update.useMutation({
        onSuccess: () => {
            router.refresh();
            toast({
                title: "Account updated",
                description: "The account has been updated successfully",
            })
        },
        onError: (error) => {
            toast({
                title: "Account update failed",
                description: error.message
            })
        }
    })

    const deleteAccount = api.account.delete.useMutation({
        onSuccess: () => {
            router.refresh();
            toast({
                title: "Account deleted",
                description: "The account has been deleted successfully",
            })
        },
        onError: (error) => {
            toast({
                title: "Account deletion failed",
                description: error.message
            })
        }
    })

    const updateAccountName = (accountId: number, newName: string) => {
        // Implement the logic to update the account name
        updateAccount.mutate({ name: newName, id: accountId });
        // This could involve setting state or making an API call
        console.log(`Updating account ${accountId} name to ${newName}`);
        // After updating, you might want to toggle off the edit mode
        toggleEditMode(accountId);
    };

    return (
        <div className="border shadow-sm rounded-lg">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Balance</TableHead>
                        <TableHead>Actions</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {allAccounts ? (
                        allAccounts.map((account) => (
                            <TableRow key={account.id}>
                                {editMode[account.id] ? (
                                    <TableCell>
                                        <input
                                            type="text"
                                            className="border-none bg-transparent outline-none"
                                            defaultValue={account.name}
                                            onBlur={(e) => updateAccountName(account.id, e.target.value)}
                                            autoFocus
                                        />
                                    </TableCell>
                                ) : (
                                    <TableCell>{account.name}</TableCell>
                                )}
                                <TableCell>0</TableCell>
                                <TableCell>
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button variant="ghost" size="icon" className="rounded-full border w-8 h-8">
                                                <span className="sr-only">Toggle account menu</span>
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end">
                                            <DropdownMenuItem onSelect={() => toggleEditMode(account.id)}>Edit</DropdownMenuItem> 
                                            <DropdownMenuItem onSelect={() => deleteAccount.mutate({id: account.id})}>Delete</DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </TableCell>
                            </TableRow>
                        ))
                    ) : (
                        <TableRow>
                            <TableCell colSpan={3}>No accounts found</TableCell>
                        </TableRow>
                    )}
                </TableBody>
            </Table>
        </div>
    )
}