import { CreateAccount } from "~/app/_components/create-account";
import { api } from "~/trpc/server";

export default async function Home() {
  const hello = await api.account.hello({ text: "from tRPX" });

  return (
    <main>
      <h1>{hello.greeting}</h1>
      <CrudShowcase />
    </main>
  );
}

async function CrudShowcase() {
  const allAccounts = await api.account.getAll()

  return (
    <div className="w-full max-w-xs">
      <h1>Accounts</h1>
      <ul>
        {allAccounts.map((account) => (
          <li key={account.id}>
            <p>{account.name}</p>
          </li>
        ))}
      </ul>

      <CreateAccount />
    </div>
  );
}
