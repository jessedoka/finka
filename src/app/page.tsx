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
      
    </main>
  );
}