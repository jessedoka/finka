"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createClient } from '../../utils/supabase/client'
import { redirect } from 'next/navigation'

import { api } from "~/trpc/react";

async function getUser() {
  const supabase = createClient()
  const { data, error } = await supabase.auth.getUser()
  if (error ?? !data?.user) {
    redirect('/login')
  }

  return { data }
}

export async function CreateAccount() {
  const router = useRouter();
  const [name, setName] = useState("");
  const { data } = await getUser();

  const createAccount = api.account.create.useMutation({
    onSuccess: () => {
      router.refresh();
      setName("");
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        createAccount.mutate({ name, user_id: data.user?.id});
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
  );
}
