import { Outlet } from 'react-router'
import Sidebar from './Sidebar'

export default function AppLayout() {
  return (
    <>
      <Sidebar />

      <main>
        <Outlet />
      </main>
    </>
  )
}
