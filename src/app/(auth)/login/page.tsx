import Link from "next/link"
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { SubmitButton } from "../../../components/submit-button"

import { createClient } from '~/utils/supabase/server'

export async function login(formData: FormData) {

  "use server"
  
  const supabase = createClient()

  if (!formData) {
    redirect('/error')
  }

  // type-casting here for convenience
  // in practice, you should validate your inputs
  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
  }

  console.log(data)

  const { error } = await supabase.auth.signInWithPassword(data)
  console.log(error)
  if (error) {
    redirect('/error')
  }

  revalidatePath('/', 'layout')
  redirect('/')
}

async function LoginPage({
  searchParams,
}: {
  searchParams: { message: string };
}) {

  return (
    <section className="bg-gray-50 dark:bg-gray-900">
      <div className="flex flex-col items-center justify-center px-6 py-8 mx-auto md:h-screen lg:py-0">
        <Link href="/" className="flex items-center mb-6 text-2xl font-semibold text-gray-900 dark:text-white">
          {/* <Logo /> */}
        </Link>

        {searchParams?.message && (
          <p className={`px-4 py-2 mb-4 text-sm text-white rounded-md`}>
            {searchParams.message}
          </p>
        )}

        <div className="w-full bg-white rounded-lg shadow dark:border md:mt-0 sm:max-w-md xl:p-0 dark:bg-gray-800 dark:border-gray-700">
          <div className="p-6 space-y-4 md:space-y-6 sm:p-8">
            <h1 className="text-xl font-bold leading-tight tracking-tight text-gray-900 md:text-2xl dark:text-white">
              Sign in to your account
            </h1>
            <form className="space-y-4 md:space-y-6">
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Your email</label>
                <input type="email" name="email" id="email" className="bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm rounded-lg focus:ring-orange-600 focus:border-orange-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-orange-500 dark:focus:border-orange-500" placeholder="example@company.com"
                  required
                />
              </div>
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Password</label>
                <input type="password" name="password" id="password" placeholder="••••••••" className="bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm rounded-lg focus:ring-orange-600 focus:border-orange-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-orange-500 dark:focus:border-orange-500"
                  required
                />
              </div>
              <div className="flex flex-col items-center">
                <label className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Confirm you are human</label>
              </div>

              {/* function not finished */}
              <div className="flex items-center justify-between">
                <Link href="#" className="text-sm font-medium text-orange-600 hover:underline dark:text-orange-500">Forgot password?</Link>
              </div>
              <SubmitButton formAction={login} />

              <p className="text-sm font-light text-gray-500 dark:text-gray-400">
                Don’t have an account yet? <Link href="/register" className="font-medium text-orange-600 hover:underline dark:text-orange-500">Sign up</Link>
              </p>
            </form>
          </div>
        </div>
      </div>
    </section>
  )
}

export default LoginPage