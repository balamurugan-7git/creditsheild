// ============================================================
// CrediShield AI – Card Components
// Composable card primitives for content sections
// ============================================================

import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// ---- Base Card ---- //
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Apply a hover shadow transition */
  hoverable?: boolean;
  /** Remove default padding from content */
  noPadding?: boolean;
}

export function Card({ hoverable = false, noPadding = false, className, children, ...rest }: CardProps) {
  return (
    <div
      className={twMerge(
        clsx(
          'rounded-xl border border-gray-200 bg-white shadow-sm',
          hoverable && 'transition-shadow duration-200 hover:shadow-md cursor-pointer',
          !noPadding && 'p-6',
        ),
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

// ---- CardHeader ---- //
export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Add a bottom border separator */
  separator?: boolean;
}

export function CardHeader({ separator = false, className, children, ...rest }: CardHeaderProps) {
  return (
    <div
      className={twMerge(
        clsx(
          'flex items-start justify-between',
          separator && 'border-b border-gray-100 pb-4 mb-4',
        ),
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

// ---- CardTitle ---- //
export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  as?: 'h1' | 'h2' | 'h3' | 'h4';
}

export function CardTitle({ as: Tag = 'h3', className, children, ...rest }: CardTitleProps) {
  return (
    <Tag
      className={twMerge('text-base font-semibold text-gray-900', className)}
      {...rest}
    >
      {children}
    </Tag>
  );
}

// ---- CardContent ---- //
export function CardContent({ className, children, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={twMerge('text-sm text-gray-600', className)} {...rest}>
      {children}
    </div>
  );
}

// ---- CardFooter ---- //
export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  separator?: boolean;
}

export function CardFooter({ separator = false, className, children, ...rest }: CardFooterProps) {
  return (
    <div
      className={twMerge(
        clsx(
          'flex items-center justify-end gap-3',
          separator && 'border-t border-gray-100 pt-4 mt-4',
        ),
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
