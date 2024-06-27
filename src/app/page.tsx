import AuthButton from "~/components/AuthButton";
import { createClient } from "~/utils/supabase/server";
import { redirect } from "next/navigation";
import { CreateAccount } from "~/components/createAccount";
import { CreateTransaction } from "~/components/createTransactions";
import { api } from "~/trpc/server";

export default async function Home() {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return redirect("/login");
  }

  return (
    <main>
      <AuthButton />
      <CrudShowcase user_id={user?.id} />
    </main>
  );
}



async function CrudShowcase({ user_id }: { user_id: string | undefined }) {

  const allAccounts = await api.account.getbyUserId({ user_id });

  return (
    <div className="w-full max-w-xs">
      <h1>Accounts</h1>
      
      {allAccounts ? (
        <ul>
          {allAccounts.map((account) => (
            <li key={account.id}>
              <p>{account.name}</p>
            </li>
          ))}
        </ul>
        ) : (
          <p>No accounts found</p>
        )}

      <CreateAccount id={user_id} />
      <CreateTransaction id={user_id} />
    </div>
  );
}