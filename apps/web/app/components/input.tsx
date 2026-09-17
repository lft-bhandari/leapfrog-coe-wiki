"use client"

import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react"

const BASE_CLASSES =
  "w-full rounded-md border border-brand-ivory bg-brand-white px-3 py-2 text-sm text-brand-abyss " +
  "placeholder:text-brand-obsidian focus:outline-none focus:ring-2 focus:ring-brand-primary " +
  "disabled:cursor-not-allowed disabled:opacity-50 transition-shadow duration-150"

type TextInputProps = InputHTMLAttributes<HTMLInputElement>

/** Single-line text field styled to brand tokens. */
export function TextInput({ className = "", ...props }: TextInputProps) {
  return <input className={`${BASE_CLASSES} h-10 ${className}`} {...props} />
}

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>

/** Multi-line text field styled to brand tokens. */
export function Textarea({ className = "", ...props }: TextareaProps) {
  return (
    <textarea
      className={`${BASE_CLASSES} min-h-[80px] resize-y py-2 ${className}`}
      {...props}
    />
  )
}
