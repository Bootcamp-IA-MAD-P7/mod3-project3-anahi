import { createAuthClient } from '@neondatabase/neon-js/auth'

export const authClient = createAuthClient(import.meta.env.VITE_NEON_AUTH_URL)

let cachedJwt = null
let cachedJwtExp = 0

function jwtExpiration(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    return payload.exp * 1000
  } catch {
    return 0
  }
}

export async function getToken() {
  if (cachedJwt && Date.now() < cachedJwtExp - 30000) return cachedJwt
  const res = await fetch(`${import.meta.env.VITE_NEON_AUTH_URL}/token`, {
    credentials: 'include',
  })
  if (!res.ok) return null
  const { token } = await res.json()
  if (!token) return null
  cachedJwt = token
  cachedJwtExp = jwtExpiration(token)
  return token
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
  cachedJwt = null
  cachedJwtExp = 0
  await authClient.signOut()
}

export async function getSession() {
  const result = await authClient.getSession()
  return result.data ?? null
}
