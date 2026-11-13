// Original flat illustration: a curry plate seen from above, with spices around it.
export default function PlateArt() {
  return (
    <svg className="plate-art" viewBox="0 0 380 400" role="img" aria-label="Illustration of a plate of curry with spices and steam">
      <g fill="none" stroke="var(--muted)" strokeWidth="2.5" strokeLinecap="round" opacity=".55">
        <path d="M150 52c-10-12 10-22 0-34" /><path d="M190 58c-10-12 10-22 0-38" /><path d="M230 52c-10-12 10-22 0-34" />
      </g>
      <g transform="translate(0 20)">
        <circle cx="190" cy="190" r="165" fill="var(--card)" stroke="var(--line)" strokeWidth="2" />
        <circle cx="190" cy="190" r="148" fill="none" stroke="var(--cardamom)" strokeWidth="1.5" strokeDasharray="1 9" strokeLinecap="round" />
        <circle cx="190" cy="190" r="132" fill="none" stroke="var(--line)" strokeWidth="1.5" />
        <circle cx="190" cy="190" r="104" fill="var(--saffron-soft)" stroke="var(--saffron)" strokeWidth="2" />
        <circle cx="190" cy="190" r="86" fill="var(--saffron)" />
        <path d="M190 190m0 0c14-2 22 10 14 20s-26 8-34-6 4-36 28-34 40 22 34 48" fill="none" stroke="var(--on-saffron)" strokeWidth="3" strokeLinecap="round" opacity=".45" />
        <g fill="var(--cardamom)">
          <ellipse cx="172" cy="170" rx="13" ry="5.5" transform="rotate(-30 172 170)" />
          <ellipse cx="206" cy="166" rx="13" ry="5.5" transform="rotate(25 206 166)" />
          <ellipse cx="192" cy="150" rx="12" ry="5" transform="rotate(88 192 150)" />
        </g>
        <g fill="none" stroke="var(--chili)" strokeWidth="4" strokeLinecap="round">
          <path d="M156 214c10 8 22 8 30 0" /><path d="M200 222c10 6 20 4 26-4" />
        </g>
        <g fill="none" stroke="var(--on-saffron)" strokeWidth="2" opacity=".7">
          <circle cx="226" cy="200" r="7" /><circle cx="150" cy="190" r="6" /><circle cx="214" cy="230" r="5" />
        </g>
        <g>
          <ellipse cx="62" cy="120" rx="22" ry="8" transform="rotate(-48 62 120)" fill="var(--cardamom-soft)" stroke="var(--cardamom)" strokeWidth="2" />
          <ellipse cx="84" cy="98" rx="22" ry="8" transform="rotate(-20 84 98)" fill="var(--cardamom-soft)" stroke="var(--cardamom)" strokeWidth="2" />
          <path d="M290 292a42 42 0 0 0 66-26z" fill="var(--cardamom-soft)" stroke="var(--cardamom)" strokeWidth="2" strokeLinejoin="round" />
          <path d="M296 288a34 34 0 0 0 52-20" fill="none" stroke="var(--cardamom)" strokeWidth="1.5" opacity=".6" />
          <path d="M44 270c18 34 54 46 86 30" fill="none" stroke="var(--chili)" strokeWidth="9" strokeLinecap="round" />
          <path d="M44 270c-6-10-2-20 8-24" fill="none" stroke="var(--cardamom)" strokeWidth="5" strokeLinecap="round" />
          <circle cx="318" cy="110" r="5" fill="var(--saffron)" /><circle cx="334" cy="128" r="3.5" fill="var(--saffron)" />
          <circle cx="306" cy="132" r="3" fill="var(--chili)" />
        </g>
      </g>
    </svg>
  );
}
