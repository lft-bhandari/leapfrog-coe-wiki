"use client"

import type { ButtonHTMLAttributes } from "react"

type Variant = "primary" | "secondary" | "ghost"
type Size = "sm" | "md" | "lg"

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    "bg-brand-primary text-brand-white hover:bg-brand-obsidian focus-visible:ring-brand-primary",
  secondary:
    "bg-brand-ivory text-brand-abyss hover:bg-brand-obsidian hover:text-brand-white focus-visible:ring-brand-obsidian",
  ghost:
    "bg-transparent text-brand-primary border border-brand-primary hover:bg-brand-mint focus-visible:ring-brand-primary",
}

const SIZE_CLASSES: Record<Size, string> = {
  sm: "h-8 px-3 text-xs",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-6 text-md",
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
}

/** Primary interactive control styled to Leapfrog brand. */
export function Button({
  variant = "primary",
  size = "md",
  className = "",
  disabled,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={[
        "inline-flex items-center justify-center gap-2 rounded-md font-normal",
        "transition-colors duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-50",
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        className,
      ].join(" ")}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
}
