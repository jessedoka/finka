import { createContext } from 'react';
export type authType = {
    token: string | null,
    setToken: (token: string | null) => void,
    logout: () => void
}

export const AuthContext = createContext<authType>({
    token: null,
    setToken: () => {},
    logout: () => {}
});

