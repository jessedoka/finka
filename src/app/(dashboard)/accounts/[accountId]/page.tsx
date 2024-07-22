import { api } from "~/trpc/server" 
import { createClient } from "~/utils/supabase/server"
import { redirect } from "next/navigation"
import TransactionsTable from "~/components/transactionTable"
import { CreateTransaction } from "~/components/createTransaction"
import { CreateBulkTransaction } from "~/components/createBulkTransaction"

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

    const accountid = parseInt(accountId);

    const allTransactions = await api.transaction.getAllbyAccountId({ accountId: accountid });

    return (
        <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-6">
            <div className="flex justify-between items-center">
                <h1 className="font-semibold text-lg md:text-2xl">Transactions</h1>
                <div className="flex space-x-3">
                    <CreateTransaction id={accountid} />
                    <CreateBulkTransaction id={accountid} />
                </div>
                
            </div>
            <TransactionsTable transactions={allTransactions} />
        </main>
    );
}

export default TransactionPage;