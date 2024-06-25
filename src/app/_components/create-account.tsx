"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "~/trpc/react";
import { createClient } from "~/utils/supabase/client";

async function signOut() {
  const supabase = createClient()
  const { error } = await supabase.auth.signOut()

  if (error) {
    console.error(error)
  }
}

export function CreateAccount({id}: {id: string | undefined}) {
  const router = useRouter();
  const [name, setName] = useState("");

  const createAccount = api.account.create.useMutation({
    onSuccess: () => {
      router.refresh();
      setName("");
    },
  });

  return (
    <div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          createAccount.mutate({ name, user_id: id});
        }}
        className="flex flex-col gap-2"
      >
        <input
          type="text"
          placeholder="Title"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded-full px-4 py-2 text-black"
        />
        <button
          type="submit"
          className="rounded-full bg-white/10 px-10 py-3 font-semibold transition hover:bg-white/20"
          disabled={createAccount.isPending}
        >
          {createAccount.isPending ? "Submitting..." : "Submit"}
        </button>
      </form>
      <button onClick={signOut}>Sign out</button>
    </div>
  );
}
