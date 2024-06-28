import React from "react"

import { api } from "../../trpc/server";
import { createClient } from "../../utils/supabase/server";
import { redirect } from "next/navigation";
import { CreateAccount } from "../../components/createAccount";
import AccountTable from "../../components/accountTable";

export default async function Account() {
    const supabase = createClient();

    const {
        data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
        return redirect("/login");
    }

    const allAccounts = await api.account.getbyUserId({ user_id: user?.id });
    
    return (
        <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-6">
            <div className="flex items-center">
                <h1 className="font-semibold text-lg md:text-2xl">Accounts</h1>
                <CreateAccount id={user?.id} />
            </div>
            <AccountTable allAccounts={allAccounts} />
        </main>
    )
}

