"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "~/trpc/react";

export function CreateTransaction({ id }: { id: string | undefined }) {
    const router = useRouter();
    const [memo, setMemo] = useState("");
    const [amount, setAmount] = useState(0);
    const [accountId, setAccountId] = useState(0);

    const CreateTransaction = api.transaction.create.useMutation({
        onSuccess: () => {
            router.refresh();
            setMemo("");
            setAmount(0);
            setAccountId(0);
        },
    });
    

    return (
        <div>
            <form
                onSubmit={(e) => {
                    e.preventDefault();
                    CreateTransaction.mutate({ memo, amount, accountId });
                }}
                className="flex flex-col gap-2"
            >
                <input
                    type="text"
                    placeholder="memo"
                    value={memo}
                    onChange={(e) => setMemo(e.target.value)}
                    className="w-full rounded-full px-4 py-2 text-black"
                />
                <input
                    type="number"
                    placeholder="Amount"
                    value={amount}
                    onChange={(e) => setAmount(parseFloat(e.target.value))}
                    className="w-full rounded-full px-4 py-2 text-black"
                />
                <input
                    type="number"
                    placeholder="Account ID"
                    value={accountId}
                    onChange={(e) => setAccountId(parseFloat(e.target.value))}
                    className="w-full rounded-full px-4 py-2 text-black"
                />
                <button
                    type="submit"
                    className="rounded-full bg-white/10 px-10 py-3 font-semibold transition hover:bg-white/20"
                    disabled={CreateTransaction.isPending}
                >
                    {CreateTransaction.isPending ? "Submitting..." : "Submit"}
                </button>
            </form>
        </div>
    );
}
