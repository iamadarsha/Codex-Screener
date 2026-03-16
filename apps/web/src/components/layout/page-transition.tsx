"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface PageTransitionProps {
  children: ReactNode;
}

const containerVariants = {
  hidden: { opacity: 0, y: 12, scale: 0.99 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.35,
      ease: [0.4, 0, 0.2, 1] as const,
      staggerChildren: 0.06,
    },
  },
  exit: { opacity: 0, y: -8, transition: { duration: 0.2 } },
};

/**
 * Uses the View Transitions API (where supported) for smooth native
 * cross-document-style transitions, with framer-motion as fallback.
 */
export function PageTransition({ children }: PageTransitionProps) {
  const pathname = usePathname();
  const prevPathRef = useRef(pathname);

  useEffect(() => {
    if (pathname === prevPathRef.current) return;
    prevPathRef.current = pathname;

    // Trigger View Transitions API if available
    if (typeof document !== "undefined" && "startViewTransition" in document) {
      (document as unknown as { startViewTransition: (cb: () => void) => void }).startViewTransition(() => {
        // The DOM update is already happening via React — this just wraps it
        // so the browser captures before/after snapshots for animation.
      });
    }
  }, [pathname]);

  return (
    <motion.div
      key={pathname}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      style={{ viewTransitionName: "page-content" }}
    >
      {children}
    </motion.div>
  );
}
