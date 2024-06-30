// TransactionsTable.tsx
"use client"

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "./ui/table";
import { Button } from "./ui/button";
import { useToast } from "./ui/use-toast";
import { api } from "../trpc/react";

type TransactionProps = {
    transactions: {
        id: number;
        memo: string;
        amount: number;
        accountId: number;
        transactionDate: Date;
        createdAt: Date;
        updatedAt: Date;
    }[];
}

export default function TransactionsTable({transactions}: TransactionProps) {
    const [editMode, setEditMode] = useState<Record<number, boolean>>({});
    const router = useRouter();
    const { toast } = useToast()

    const toggleEditMode = (transactionId: number) => {
        setEditMode((prev) => ({ ...prev, [transactionId]: !prev[transactionId] }));
    };

    const updateTransaction = api.transaction.update.useMutation({
        onSuccess: () => {
            router.refresh();
            toast({
                title: "Transaction updated",
                description: "The Transaction has been updated successfully",
            })
        },
        onError: (error) => {
            toast({
                title: "Transaction update failed",
                description: error.message
            })
        }
    })

    const updateTransactionMemo = (transactionId: number, newMemo: string) => {
        if (newMemo === "") {
            toast({
                title: "Transaction Memo cannot be empty",
                description: "Please enter a valid Transaction Memo",
            });
            return;
        }

        if (newMemo === transactions.find((transaction) => transaction.id === transactionId)?.memo) {
            toggleEditMode(transactionId);
            return;
        }




        updateTransaction.mutate({
            memo: newMemo, id: transactionId,
            accountId: 0,
            amount: 0
        });
        toggleEditMode(transactionId);
    };

    const deleteTransaction = api.transaction.delete.useMutation({
        onSuccess: () => {
            router.refresh();
            toast({
                title: "Transaction deleted",
                description: "The Transaction has been deleted successfully",
            })
        },
        onError: (error) => {
            toast({
                title: "Transaction deletion failed",
                description: error.message
            })
        }
    })

    return (
        <div className="border shadow-sm rounded-lg">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Memo</TableHead>
                        <TableHead>Amount</TableHead>
                        <TableHead>Actions</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {transactions ? (
                        transactions.map((transaction) => (
                            <TableRow key={transaction.id}>
                                <TableCell>{transaction.transactionDate.toLocaleString()}</TableCell>
                                {editMode[transaction.id] ? (
                                    <TableCell>
                                        <input
                                            type="text"
                                            className="border-none bg-transparent outline-none"
                                            defaultValue={transaction.memo}
                                            onBlur={(e) => updateTransactionMemo(transaction.id, e.target.value)}
                                            autoFocus
                                        />
                                    </TableCell>
                                ) : (
                                    <TableCell>{transaction.memo}</TableCell>
                                )}
                                <TableCell>{transaction.amount}</TableCell>
                                <TableCell className="flex space-x-3">
                                    <Button onClick={() => toggleEditMode(transaction.id)}>
                                        {editMode[transaction.id] ? "Cancel" : "Edit"}
                                    </Button>
                                    {editMode[transaction.id] ? "" : (
                                        <div className="space-x-3">
                                            <Button onClick={() => deleteTransaction.mutate({ id: transaction.id })}>
                                                {deleteTransaction.isPending ? "Deleting..." : "Delete"}
                                            </Button>
                                        </div>
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
    );
}
