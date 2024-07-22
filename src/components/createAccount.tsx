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
    name: z.string().min(2, {
        message: "name must be at least 2 characters.",
    }),
})


export function CreateAccount({ id }: { id: string | undefined }) {
    const router = useRouter();
    const { toast } = useToast();
    const [isVisible, setIsVisible] = useState(false);

    const toggleOverlay = () => {
        setIsVisible(!isVisible);
    };

    const createAccount = api.account.create.useMutation({
        onSuccess: () => {
            router.refresh();
            toast({
                title: "Account created",
                description: "The account has been created successfully",
            })
        },
        onError: (error) => {
            toast({
                title: "Account creation failed",
                description: error.message
            })
        }
    })

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
        },
    })

    function onSubmit(values: z.infer<typeof formSchema>) {
        createAccount.mutate({ name: values.name, user_id: id});
        toggleOverlay();
    }

    return (
        <div className='ml-auto'>
            <Button size="sm" onClick={toggleOverlay}>Add Accounts</Button>

            {isVisible && (
                <div className="fixed inset-0 flex items-center justify-center z-50">
                    <div className="fixed inset-0 bg-black opacity-50 backdrop-blur-sm"></div>
                    <div className="relative z-10 bg-secondary p-4 rounded shadow-lg">
                        <Form {...form}>
                            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                                <FormField
                                    control={form.control}
                                    name="name"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Account Name</FormLabel>
                                            <FormControl>
                                                <Input placeholder="name" {...field} />
                                            </FormControl>
                                            <FormDescription>
                                                This is your public display name.
                                            </FormDescription>
                                            <FormMessage />
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
};
