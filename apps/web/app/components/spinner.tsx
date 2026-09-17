type SpinnerSize = "sm" | "md" | "lg"

const SIZE_CLASSES: Record<SpinnerSize, string> = {
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-10 w-10 border-4",
}

interface SpinnerProps {
  size?: SpinnerSize
  label?: string
}

/** Circular loading indicator in brand primary green. */
export function Spinner({ size = "md", label = "Loading…" }: SpinnerProps) {
  return (
    <span className="inline-flex items-center gap-2" role="status" aria-label={label}>
      <span
        className={[
          "animate-spin rounded-full border-brand-ivory border-t-brand-primary",
          SIZE_CLASSES[size],
        ].join(" ")}
      />
      <span className="sr-only">{label}</span>
    </span>
  )
}
