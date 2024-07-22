"use client";

import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { Button } from "./ui/button"
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "./ui/form"
import { Input } from "./ui/input"
import { useState } from 'react';
import { api } from "~/trpc/react";
import { useRouter } from 'next/navigation';
import { useToast } from "./ui/use-toast";

const formSchema = z.object({
    memo: z.string().min(2, {
        message: "memo must be at least 2 characters.",
    }),
    amount: z.number(),
    accountId: z.number()
})

export function CreateTransaction({ id }: { id: number }) {
    const router = useRouter();
    const { toast } = useToast();
    const [isVisible, setIsVisible] = useState(false);

    const toggleOverlay = () => {
        setIsVisible(!isVisible);
    };

    const CreateTransaction = api.transaction.create.useMutation({
        onSuccess: () => {
            router.refresh();
            toast({
                title: "Transaction created",
                description: "The transaction has been created successfully",
            })
        },
        onError: (error) => {
            toast({
                title: "Transaction creation failed",
                description: error.message
            })
        }
    })

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            memo: "",
            amount: 0,
            accountId: 0,
        },
    })

    function onSubmit(data: z.infer<typeof formSchema>) {
        CreateTransaction.mutate({ memo: data.memo, amount: data.amount, accountId: id });
        toggleOverlay();
    }

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        // Convert the input value to an integer before passing it to the onChange handler
        if (isNaN(parseInt(e.target.value, 10))) {
            return;
        }
        
        const intValue = parseInt(e.target.value, 10);
        form.setValue("amount", intValue);
    };
    

    return (
        <div className='ml-auto'>
            <Button size="sm" onClick={toggleOverlay}>Add Transactions</Button>

            {isVisible && (
                <div className="fixed inset-0 flex items-center justify-center z-50">
                    <div className="fixed inset-0 bg-black opacity-80 backdrop-blur-sm"></div>
                    <div className="relative z-10 bg-secondary p-4 rounded shadow-lg">
                        <Form {...form}>
                            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                                <FormField
                                    control={form.control}
                                    name="memo"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Memo</FormLabel>
                                            <Input {...field} />
                                            <FormDescription>Enter a memo for the transaction</FormDescription>
                                            <FormMessage {...field} />
                                        </FormItem>
                                    )}
                                />
                                <FormField
                                    control={form.control}
                                    name="amount"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Amount</FormLabel>
                                            <Input  {...field} value={String(field.value)} onChange={handleInputChange} />
                                            <FormDescription>Enter the amount for the transaction</FormDescription>
                                            <FormMessage {...field} />
                                        </FormItem>
                                    )}
                                />
                                <div className="flex justify-between gap-4">
                                    <Button variant="ghost" type="submit">Submit</Button>
                                    <Button variant="destructive" onClick={toggleOverlay}>Close</Button>
                                </div>
                            </form>
                        </Form>
                    </div>
                </div>
            )}
        </div>
    );
}
