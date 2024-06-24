import Link from "next/link";

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
  const latestAccount = await api.account.getLatest();

  return (
    <div className="w-full max-w-xs">
      {latestAccount ? (
        <p className="truncate">Your most recent post: {latestAccount.name}</p>
      ) : (
        <p>You have no account yet.</p>
      )}

      <CreateAccount />
    </div>
  );
}
