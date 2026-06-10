import Image from "next/image";
import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <p className="text-sm font-light text-gray-500">
          Have an account? <Link href="/login"
            className="font-medium text-orange-600 hover:underline dark:text-orange-500">Login here</Link>
        </p>
      </main>
    </div>
  );
}
