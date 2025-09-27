'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import styles from './Sidebar.module.css';

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className={styles.sidebar}>
      <div className={styles.sidebarHeader}>
        <h2>Document App</h2>
      </div>
      <ul className={styles.sidebarMenu}>
        <li>
          <Link
            href="/"
            className={`${styles.sidebarLink} ${pathname === '/' ? styles.active : ''}`}
          >
            <span className={styles.icon}>📤</span>
            Upload Document
          </Link>
        </li>
        <li>
          <Link
            href="/documents"
            className={`${styles.sidebarLink} ${pathname === '/documents' ? styles.active : ''}`}
          >
            <span className={styles.icon}>📄</span>
            View Documents
          </Link>
        </li>
        <li>
          <Link
            href="/extractions"
            className={`${styles.sidebarLink} ${pathname === '/extractions' ? styles.active : ''}`}
          >
            <span className={styles.icon}>📊</span>
            View Extractions
          </Link>
        </li>
      </ul>
    </nav>
  );
}