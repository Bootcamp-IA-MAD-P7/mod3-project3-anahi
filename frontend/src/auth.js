import { createAuthClient } from '@neondatabase/neon-js/auth'

export const authClient = createAuthClient(import.meta.env.VITE_NEON_AUTH_URL)

export async function getToken() {
  const result = await authClient.getSession()
  return result.data?.session?.token ?? null
}

export async function signIn(email, password) {
  const result = await authClient.signIn.email({ email, password })
  if (result.error) throw new Error(result.error.message)
  return result
}

export async function signUp(email, password) {
  const result = await authClient.signUp.email({
    email,
    password,
    name: email.split('@')[0],
  })
  if (result.error) throw new Error(result.error.message)
  return result
}

export async function signOut() {
  await authClient.signOut()
}

export async function getSession() {
  const result = await authClient.getSession()
  return result.data ?? null
}
