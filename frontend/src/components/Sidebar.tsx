import { NavLink } from "react-router-dom";

import { logout, type CurrentUser } from "../api";
import styles from "./Sidebar.module.css";

function LibraryIcon() {
  return (
    <svg viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.4">
      <path d="M3 4.5A1.5 1.5 0 0 1 4.5 3H10v14H4.5A1.5 1.5 0 0 1 3 15.5v-11Z" />
      <path d="M17 4.5A1.5 1.5 0 0 0 15.5 3H10v14h5.5a1.5 1.5 0 0 0 1.5-1.5v-11Z" />
    </svg>
  );
}

function UploadIcon() {
  return (
    <svg
      viewBox="0 0 20 20"
      width="18"
      height="18"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M10 13V4M10 4 6.5 7.5M10 4l3.5 3.5" />
      <path d="M4 14v1.5A1.5 1.5 0 0 0 5.5 17h9a1.5 1.5 0 0 0 1.5-1.5V14" />
    </svg>
  );
}

interface SidebarProps {
  user: CurrentUser | null;
}

export function Sidebar({ user }: SidebarProps) {
  async function handleLogout() {
    await logout();
    window.location.href = "/login";
  }

  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>BookerSoft</div>

      <nav className={styles.nav}>
        <NavLink
          to="/"
          end
          className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ""}`}
        >
          <LibraryIcon />
          <span>Library</span>
        </NavLink>
        <NavLink to="/upload" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ""}`}>
          <UploadIcon />
          <span>Upload</span>
        </NavLink>
      </nav>

      <div className={styles.account}>
        <span className={styles.username}>{user?.username}</span>
        <button type="button" className={styles.logoutButton} onClick={handleLogout}>
          Log out
        </button>
      </div>
    </aside>
  );
}
