import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "../../lib/cn";
import { fieldInput, fieldInputWithIcon } from "../../lib/design";

interface FormFieldBaseProps {
  id: string;
  label: string;
  icon?: LucideIcon;
  hint?: ReactNode;
  className?: string;
}

type FormFieldInputProps = FormFieldBaseProps &
  Omit<InputHTMLAttributes<HTMLInputElement>, "id" | "className"> & {
    multiline?: false;
  };

type FormFieldTextareaProps = FormFieldBaseProps &
  Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "id" | "className"> & {
    multiline: true;
  };

export function FormField(props: FormFieldInputProps | FormFieldTextareaProps) {
  const { id, label, icon: Icon, hint, className, multiline, ...rest } = props;

  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-neutral-700">
        {label}
      </label>
      <div className="relative">
        {Icon && (
          <Icon
            className={cn(
              "pointer-events-none absolute left-3.5 size-4 text-neutral-400",
              multiline ? "top-3.5" : "top-1/2 -translate-y-1/2"
            )}
            strokeWidth={2}
            aria-hidden="true"
          />
        )}
        {multiline ? (
          <textarea
            id={id}
            className={cn(fieldInput, Icon && "pl-10", "resize-y")}
            {...(rest as TextareaHTMLAttributes<HTMLTextAreaElement>)}
          />
        ) : (
          <input
            id={id}
            className={cn(Icon ? fieldInputWithIcon : fieldInput)}
            {...(rest as InputHTMLAttributes<HTMLInputElement>)}
          />
        )}
      </div>
      {hint && <p className="mt-1.5 text-xs text-neutral-500">{hint}</p>}
    </div>
  );
}
