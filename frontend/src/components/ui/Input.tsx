// ============================================================
// CrediShield AI – Reusable Input Component
// ============================================================

import React, { forwardRef, useId } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// ---- Props ---- //
export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftAddon?: React.ReactNode;
  rightAddon?: React.ReactNode;
  fullWidth?: boolean;
  containerClassName?: string;
}

// ---- Component ---- //
const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leftAddon,
      rightAddon,
      fullWidth = true,
      containerClassName,
      className,
      id: providedId,
      required,
      disabled,
      ...rest
    },
    ref,
  ) => {
    const generatedId = useId();
    const id = providedId ?? generatedId;
    const hasError = Boolean(error);

    return (
      <div
        className={twMerge(
          clsx('flex flex-col gap-1', fullWidth && 'w-full'),
          containerClassName,
        )}
      >
        {/* Label */}
        {label && (
          <label
            htmlFor={id}
            className={clsx(
              'text-sm font-medium',
              hasError ? 'text-danger-600' : 'text-gray-700',
            )}
          >
            {label}
            {required && <span className="ml-0.5 text-danger-500">*</span>}
          </label>
        )}

        {/* Input wrapper */}
        <div className={clsx('relative flex items-center', fullWidth && 'w-full')}>
          {/* Left addon (icon / prefix) */}
          {leftAddon && (
            <div className="pointer-events-none absolute left-3 flex items-center text-gray-400">
              {leftAddon}
            </div>
          )}

          <input
            id={id}
            ref={ref}
            disabled={disabled}
            aria-invalid={hasError}
            aria-describedby={
              hasError ? `${id}-error` : helperText ? `${id}-helper` : undefined
            }
            className={twMerge(
              clsx(
                'block rounded-lg border text-sm transition-colors duration-150',
                'placeholder:text-gray-400',
                'focus:outline-none focus:ring-2 focus:ring-offset-0',
                fullWidth ? 'w-full' : '',
                leftAddon ? 'pl-9' : 'pl-3',
                rightAddon ? 'pr-9' : 'pr-3',
                'py-2',
                hasError
                  ? 'border-danger-400 bg-danger-50 text-danger-900 focus:border-danger-500 focus:ring-danger-300'
                  : 'border-gray-300 bg-white text-gray-900 focus:border-primary-500 focus:ring-primary-200',
                disabled && 'cursor-not-allowed bg-gray-100 text-gray-400',
              ),
              className,
            )}
            {...rest}
          />

          {/* Right addon (icon / suffix) */}
          {rightAddon && (
            <div className="absolute right-3 flex items-center text-gray-400">
              {rightAddon}
            </div>
          )}
        </div>

        {/* Error message */}
        {hasError && (
          <p id={`${id}-error`} className="text-xs text-danger-600" role="alert">
            {error}
          </p>
        )}

        {/* Helper text */}
        {!hasError && helperText && (
          <p id={`${id}-helper`} className="text-xs text-gray-500">
            {helperText}
          </p>
        )}
      </div>
    );
  },
);

Input.displayName = 'Input';

export default Input;
