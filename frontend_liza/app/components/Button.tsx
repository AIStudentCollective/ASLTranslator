"use client";

import { forwardRef } from "react";
import clsx from "clsx";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  fullWidth?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, className, fullWidth = false, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={clsx(
          "bg-blue-200 text-black font-medium py-2 px-4 rounded-md shadow hover:bg-blue-300 transition",
          fullWidth && "w-full",
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
