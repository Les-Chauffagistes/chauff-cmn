import type { ReactNode } from "react";
import Link from "next/link";
import Image from "next/image";

export interface FooterLink {
  label: string;
  href: string;
  external?: boolean;
  icon?: ReactNode;
}

export interface FooterSection {
  title: string;
  links: FooterLink[];
}

export interface FooterProps {
  logoSrc: string;
  logoAlt: string;
  brandName: string;
  brandHref: string;
  tagline: string;
  sections: FooterSection[];
  bottomText: string;
  bottomSubtext?: string;
}

// Nécessite les custom properties CSS --text-main, --text-muted, --bg-alt,
// --border-color et --max-width définies par l'app hôte (mêmes noms que
// pool-site/globals.css), et le stylesheet "@chauffagistes/cmn/ui/footer.css"
// importé une fois par l'app hôte (ex. dans son layout racine).
export function Footer({ logoSrc, logoAlt, brandName, brandHref, tagline, sections, bottomText, bottomSubtext }: Readonly<FooterProps>) {
  return (
    <footer className="chauffcmn-footer">
      <div className="chauffcmn-footer-inner">
        <div className="chauffcmn-footer-brand">
          <Link href={brandHref}>
            <Image src={logoSrc} width={32} height={32} alt={logoAlt} style={{ borderRadius: "50%" }} />
            <h3>{brandName}</h3>
          </Link>
          <p>{tagline}</p>
        </div>

        {sections.map(section => (
          <div className="chauffcmn-footer-category" key={section.title}>
            <h4>{section.title}</h4>
            {section.links.map(link => (
              <Link key={link.label} href={link.href} target={link.external ? "_blank" : undefined}>
                {link.icon}
                <p>{link.label}</p>
              </Link>
            ))}
          </div>
        ))}
      </div>

      <div className="chauffcmn-footer-bottom">
        <p>{bottomText}</p>
        {bottomSubtext && <p>{bottomSubtext}</p>}
      </div>
    </footer>
  );
}
