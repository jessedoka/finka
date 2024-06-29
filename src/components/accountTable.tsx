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

    const updateAccountName = (accountId: number, newName: string) => {
        if (newName === "") {
            toast({
                title: "Account name cannot be empty",
                description: "Please enter a valid account name",
            });
            return;
        }

        if (newName === allAccounts.find((account) => account.id === accountId)?.name) {
            toggleEditMode(accountId);
            return;
        }


        updateAccount.mutate({ name: newName, id: accountId });
        toggleEditMode(accountId);
    };

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
                                <TableCell className="space-x-3"> 
                                    <Button onClick={() => toggleEditMode(account.id)}>
                                        {editMode[account.id] ? "Cancel" : "Edit"}
                                    </Button> 
                                    {editMode[account.id] ? "" : (
                                        <Button onClick={() => deleteAccount.mutate({ id: account.id })}>
                                            {editMode[account.id] ? "" : deleteAccount.isPending ? "Deleting..." : "Delete"}

                                        </Button>
                                    )}
                    
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