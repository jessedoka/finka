import { createClient } from "~/utils/supabase/server";
import Link from "next/link";
import { redirect } from "next/navigation";
import { CreateAccount } from "~/components/create-account";
import { api } from "~/trpc/server";

export default async function AuthButton() {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  const signOut = async () => {
    "use server";

    const supabase = createClient();
    await supabase.auth.signOut();
    return redirect("/login");
  };

  return user ? (
    <div className="flex items-center gap-4">
      Hey, {user.email}!
      <CrudShowcase id={user?.id} />
      <form action={signOut}>
        <button className="py-2 px-4 rounded-md no-underline bg-btn-background hover:bg-btn-background-hover">
          Logout
        </button>
      </form>
    </div>
  ) : (
    <Link
      href="/login"
      className="py-2 px-3 flex rounded-md no-underline bg-btn-background hover:bg-btn-background-hover"
    >
      Login
    </Link>
  );
}

async function CrudShowcase({ id }: { id: string | undefined }) {
  const allAccounts = await api.account.getbyUserId({ id });

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

      <CreateAccount id={id} />
    </div>
  );
}
