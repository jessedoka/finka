"use client"

import { AuthContext } from "@/context/auth";
import { useState } from "react";

function AuthProvider({ children }: Readonly<{children: React.ReactNode}>) {
    let [token, setToken] = useState<string | null>(null);
    let authObject = {
        token,
        setToken, 
        logout: () => {
            setToken(null)
        }
    }; 

    return (
        <div>
            <AuthContext.Provider value={authObject}>
                {children}
            </AuthContext.Provider>
        </div>
    )
}

export default AuthProvider