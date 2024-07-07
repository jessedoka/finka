import Link from "next/link"
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { SubmitButton } from "../../../components/submit-button"
import Logo from "../../../components/logo"
import { createClient } from '~/utils/supabase/server'

export async function signup(formData: FormData) {
    "use server"

    const supabase = createClient()

    // type-casting here for convenience
    // in practice, you should validate your inputs
    const data = {
        email: formData.get('email') as string,
        password: formData.get('password') as string,
    }

    const { error } = await supabase.auth.signUp(data)

    if (error) {
        redirect('/error')
    }

    revalidatePath('/', 'layout')
    redirect('/')
}

async function RegisterPage({
    searchParams,
}: {
    searchParams: { message: string };
}) {

    return (
        <section className="bg-background">
            <div className="flex flex-col items-center justify-center px-6 py-8 mx-auto md:h-screen lg:py-0">
                <Link href="/" className="flex items-center mb-6">
                    <Logo />
                </Link>

                {/* message */}
                {searchParams?.message && (
                    <p className={`px-4 py-2 mb-4 text-sm text-white rounded-md`}>
                        {searchParams.message}
                    </p>
                )}

                <div className="w-full rounded-lg shadow dark:border md:mt-0 sm:max-w-md xl:p-0 bg-secondary border-white">
                    <div className="p-6 space-y-4 md:space-y-6 sm:p-8">
                        <h1 className="text-xl font-bold leading-tight tracking-tight md:text-2xl">
                            Create Account
                        </h1>
                        <form className="space-y-4 md:space-y-6">
                            <div>
                                <label className="block mb-2 text-sm font-medium">Your email</label>

                                <input type="email" className="border text-gray-900 sm:text-sm rounded-lg block w-full p-2.5" placeholder="example@company.com"
                                    
                                />
                            </div>
                            <div>
                                <label className="block mb-2 text-sm font-medium">Password</label>
                                <input type="password" name="password" id="password" placeholder="••••••••" className="border text-gray-900 sm:text-sm rounded-lg block w-full p-2.5" 
                                />
                            </div>
                            <div>
                                <label className="block mb-2 text-sm font-medium">Confirm password</label>
                                <input type="password" name="confirm-password" id="confirm-password" placeholder="••••••••" className="border text-gray-900 sm:text-sm rounded-lg block w-full p-2.5"
                                    />
                            </div>

                            {/* for later */}
                            <div className="flex items-start">
                                <div className="flex items-center h-5">
                                    <input id="terms" aria-describedby="terms" type="checkbox" className="w-4 h-4 border border-gray-300 rounded bg-gray-50 focus:ring-3 focus:ring-primary-300 dark:bg-gray-700 dark:border-gray-600 dark:focus:ring-primary-600 dark:ring-offset-gray-800" required />
                                </div>
                                <div className="ml-3 text-sm">
                                    <label className="font-light text-gray-500 dark:text-gray-300">I accept the <Link className="font-medium text-primary-600 hover:underline dark:text-primary-500" href="#">Terms and Conditions</Link></label>
                                </div>
                            </div>
                            <SubmitButton formAction={signup} pendingText="Loading">
                                Sign up
                            </SubmitButton>

                            <p className="text-sm font-light text-gray-500">
                                Already have an account? <Link href="/login"
                                    className="font-medium text-orange-600 hover:underline dark:text-orange-500">Login here</Link>
                            </p>
                        </form>
                    </div>
                </div>
            </div>
        </section>
    )
}

export default RegisterPage