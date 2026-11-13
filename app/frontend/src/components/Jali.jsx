// A carved-screen (jali) geometric pattern, drawn as a repeating SVG tile.
// Colors come from the theme variables, so it follows light and dark mode.
export default function Jali({ className = "" }) {
  return (
    <svg className={className} width="100%" height="100%" aria-hidden="true" focusable="false">
      <defs>
        <pattern id="jali" width="56" height="56" patternUnits="userSpaceOnUse">
          <path d="M28 4 L52 28 L28 52 L4 28Z" fill="none" stroke="var(--saffron)" strokeWidth="1" />
          <g fill="none" stroke="var(--cardamom)" strokeWidth="1">
            <rect x="16" y="16" width="24" height="24" />
            <rect x="16" y="16" width="24" height="24" transform="rotate(45 28 28)" />
          </g>
          <circle cx="28" cy="28" r="2.5" fill="var(--saffron)" />
          <g fill="var(--saffron)">
            <circle cx="0" cy="0" r="2" /><circle cx="56" cy="0" r="2" />
            <circle cx="0" cy="56" r="2" /><circle cx="56" cy="56" r="2" />
          </g>
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#jali)" />
    </svg>
  );
}
