import { createBrowserRouter } from 'react-router'
import AppLayout from './AppLayout'
import Home from '../pages/Home'
import Chat from '../pages/Chat'


// /login sits outside AppLayout — a logged-out visitor shouldn't see the
// authenticated nav. Everything under "/" does, via AppLayout's <Outlet/>.
// No auth guard yet: every route below is reachable by anyone for now.
export const router = createBrowserRouter([

  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Home /> },
      { path: 'chat', element: <Chat /> }
    ],
  },
])
