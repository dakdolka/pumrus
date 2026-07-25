export default function BrandLogo({ className = "brand-logo" }) {
  return (
    <svg className={className} viewBox="-8 0 308 96" aria-label="UmRus" role="img">
      <g className="brand-u" fill="none" strokeLinecap="round" strokeLinejoin="round">
        <path d="M28 35v21c0 15 10 25 24 25s24-10 24-25V35" strokeWidth="10" />
      </g>
      <g className="brand-cap" transform="rotate(-14 27 25)" fill="none" strokeLinecap="round" strokeLinejoin="round">
        <path d="M-2 23 27 10l29 14-30 13L-2 23Z" strokeWidth="3" />
        <path d="M12 31v8c8 4 20 4 28 0v-8" strokeWidth="3" />
        <path d="M-1 24-5 43" strokeWidth="2.5" />
        <path d="m-5 43-3 8m3-8 3 8" strokeWidth="2.5" />
      </g>
      <text x="86" y="81" fontSize="55" fontWeight="800" letterSpacing="-2">mRus</text>
    </svg>
  );
}
