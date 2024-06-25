import { CreateAccount } from "~/app/_components/create-account";
import { api } from "~/trpc/server";
import { createClient } from "~/utils/supabase/server";

const supabase = createClient()


export default async function Home() {
  const { data } = await getUser();
  const hello = await api.account.hello({ text: data.user?.email ?? "world"});

  return (
    <main>
      <h1>{hello.greeting}</h1>
      <CrudShowcase id={data.user?.id}/>
     
    </main>
  );
}

async function CrudShowcase({id}: {id: string | undefined}) {
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

      <CreateAccount id={id}/>
    </div>
  );
}

async function getUser() {
  const { data, error } = await supabase.auth.getUser()
  if (error ?? !data?.user) {
    console.error(error)
  }

  return { data }
}

