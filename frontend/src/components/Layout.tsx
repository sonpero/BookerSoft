import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";

import { fetchCurrentUser, type CurrentUser } from "../api";
import { MobileHeader, MobileNav, Sidebar } from "./Sidebar";
import styles from "./Layout.module.css";

export function Layout() {
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    fetchCurrentUser().then(setUser);
  }, []);

  return (
    <div className={styles.shell}>
      <Sidebar user={user} />
      <MobileHeader user={user} />
      <main className={styles.main}>
        <Outlet context={user} />
      </main>
      <MobileNav />
    </div>
  );
}
