import * as React from "react";

import { cn } from "@/lib/utils";

export const Label = React.forwardRef<
  HTMLLabelElement,
  React.LabelHTMLAttributes<HTMLLabelElement>
>(({ className, ...props }, ref) => (
  <label
    ref={ref}
    className={cn(
      "mb-1.5 block text-xs font-medium uppercase tracking-wide text-white/50",
      className,
    )}
    {...props}
  />
));
Label.displayName = "Label";
