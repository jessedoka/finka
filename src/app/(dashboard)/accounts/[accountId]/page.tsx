import { api } from "~/trpc/server" 
import { createClient } from "~/utils/supabase/server"
import { redirect } from "next/navigation"
import TransactionsTable from "~/components/transactionTable"

// get params from the URL

async function TransactionPage({ params } : {params: { accountId: string }}) {
   
    const { accountId } = params

    const supabase = createClient();

    const {
        data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
        return redirect("/login");
    }

    if (!accountId || Array.isArray(accountId)) {
        return <div>Invalid account ID</div>;
    }

    const allTransactions = await api.transaction.getAllbyAccountId({ accountId: parseInt(accountId) });

    return (
        <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-6">
            <div className="flex items-center">
                <h1 className="font-semibold text-lg md:text-2xl">Transactions</h1>
                {/* <CreateTransaction id={user?.id} /> */}
            </div>
            <TransactionsTable transactions={allTransactions} />
        </main>
    );
}

export default TransactionPage;