import { api } from "~/trpc/server"

async function TransactionPage({ accountId }: { accountId: number }) {
    // if (!accountId) {
    //     return <div>Account ID is required</div>;
    // }

    const allTransactions = await api.transaction.getAllbyAccountId({ accountId });

    return ( 
        <div>
            <h1>Transaction Page</h1>
            <p>Account ID: {accountId}</p>

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