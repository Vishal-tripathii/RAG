import { NavLink } from 'react-router'
import { ChatIcon, HomeIcon } from './icons'

const links = [
  { to: '/', label: 'Home', icon: HomeIcon, end: true },
  { to: '/chat', label: 'Chat', icon: ChatIcon, end: false },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      {links.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          title={label}
          aria-label={label}
          className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
        >
          <Icon />
        </NavLink>
      ))}
    </aside>
  )
}
