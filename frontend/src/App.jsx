import { useEffect, useRef, useState } from 'react'
import { getSession } from './auth'
import Login from './screens/Login'
import Onboarding from './screens/Onboarding'
import Generate from './screens/Generate'
import Settings from './screens/Settings'

export default function App() {
  const [screen, setScreen] = useState(null)
  const [userContext, setUserContext] = useState('')
  const initialized = useRef(false)

  useEffect(() => {
    if (initialized.current) return
    initialized.current = true

    getSession().then((session) => {
      if (!session?.user) {
        setScreen('login')
        return
      }
      // fetch user context — if empty show onboarding, else generate
      import('./api').then(({ getMe }) =>
        getMe().then((me) => {
          if (me?.user_context) {
            setUserContext(me.user_context)
            setScreen('generate')
          } else {
            setScreen('onboarding')
          }
        })
      )
    })
  }, [])

  if (!screen) return null

  return (
    <>
      {screen === 'login' && <Login onSuccess={(ctx) => {
        if (ctx) { setUserContext(ctx); setScreen('generate') }
        else setScreen('onboarding')
      }} />}
      {screen === 'onboarding' && <Onboarding onSave={(ctx) => {
        setUserContext(ctx); setScreen('generate')
      }} />}
      {screen === 'generate' && <Generate
        userContext={userContext}
        onSettings={() => setScreen('settings')}
      />}
      {screen === 'settings' && <Settings
        userContext={userContext}
        onSave={(ctx) => { setUserContext(ctx); setScreen('generate') }}
        onCancel={() => setScreen('generate')}
        onSignOut={() => setScreen('login')}
      />}
    </>
  )
}
