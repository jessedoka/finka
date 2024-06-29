import { api } from "~/trpc/server"

// get params from the URL

async function TransactionPage({ params }: { params: { accountId: number } }) {
    if (!params.accountId) {
        return <div>Account ID not found</div>;
    }

    if (typeof params.accountId !== "number") {
        return <div>Account ID must be a number {params.accountId}</div>;
    }
   

    const allTransactions = await api.transaction.getAllbyAccountId({ accountId: params.accountId });

    return ( 
        <div>
            <h1>Transaction Page</h1>
            <p>Account ID: {params.accountId}</p>

            <ul>
                {allTransactions.map((transaction) => (
                    <li key={transaction.id}>
                        {transaction.memo} - {transaction.amount}
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default TransactionPage;