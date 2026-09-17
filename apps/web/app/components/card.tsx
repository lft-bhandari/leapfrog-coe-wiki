import type { HTMLAttributes } from "react"

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Adds an extra 1px border ring; useful for content that sits on white. */
  bordered?: boolean
}

/** Content panel with brand-consistent background, padding, and shadow. */
export function Card({ bordered = false, className = "", children, ...props }: CardProps) {
  return (
    <div
      className={[
        "rounded-lg bg-brand-white p-6 shadow-sm",
        bordered ? "ring-1 ring-brand-ivory" : "",
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </div>
  )
}
