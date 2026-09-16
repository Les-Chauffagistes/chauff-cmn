"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { ExternalLink } from "lucide-react";

export interface NavbarLink {
  label: string;
  href: string;
  external?: boolean;
  // Par défaut le lien est actif dès que le pathname commence par `href`
  // (utile pour des sous-routes comme /pool/stats). Passer `exact: true`
  // pour n'activer le lien que sur une correspondance exacte du pathname
  // (utile quand un autre lien du menu a `href` comme préfixe, ex. "/pool"
  // face à "/pool/stats").
  exact?: boolean;
}

export interface NavbarProps {
  logoSrc: string;
  logoAlt: string;
  homeHref?: string;
  links: NavbarLink[];
}

// Nécessite les custom properties CSS --text-main et --text-muted définies
// par l'app hôte (mêmes noms que pool-site/globals.css).
export function Navbar({ logoSrc, logoAlt, homeHref = "/", links }: Readonly<NavbarProps>) {
  const path = usePathname();

  return (
    <nav style={{
      position: "fixed",
      top: 14,
      left: "50%",
      transform: "translateX(-50%)",
      zIndex: 100,
      display: "flex",
      alignItems: "center",
      gap: 8,
      padding: "10px 20px",
      borderRadius: 999,
      background: "rgba(14, 14, 17, 0.6)",
      backdropFilter: "blur(16px)",
      WebkitBackdropFilter: "blur(16px)",
      border: "1px solid rgba(255, 255, 255, 0.08)",
      boxShadow: "0 4px 24px rgba(0, 0, 0, 0.3)",
    }}>
      <Link href={homeHref} style={{
        display: "flex",
        alignItems: "center",
        marginRight: 8,
      }}>
        <Image
          src={logoSrc}
          width={28}
          height={28}
          alt={logoAlt}
          style={{ borderRadius: "50%" }}
        />
      </Link>

      {links.map(link => {
        const isActive = !link.external && (link.exact ? path === link.href : path.startsWith(link.href));

        return (
          <Link
            key={link.label}
            href={link.href}
            target={link.external ? "_blank" : undefined}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
              padding: "6px 14px",
              borderRadius: 999,
              fontSize: "0.85rem",
              fontWeight: isActive ? 600 : 500,
              color: isActive ? "var(--text-main)" : "var(--text-muted)",
              background: isActive ? "rgba(255, 255, 255, 0.08)" : "transparent",
              textDecoration: "none",
              transition: "color 0.2s, background 0.2s",
            }}
            onMouseEnter={e => {
              if (!isActive) {
                e.currentTarget.style.color = "var(--text-main)";
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.06)";
              }
            }}
            onMouseLeave={e => {
              if (!isActive) {
                e.currentTarget.style.color = "var(--text-muted)";
                e.currentTarget.style.background = "transparent";
              }
            }}
          >
            {link.label}
            {link.external && <ExternalLink size={12} />}
          </Link>
        );
      })}
    </nav>
  );
}
