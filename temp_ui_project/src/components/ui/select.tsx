import React from 'react';
import styles from './Select.module.css';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'aria-invalid' | 'aria-required' | 'aria-describedby' | 'aria-label' | 'aria-labelledby'> {
  /** Unique identifier for the select element */
  id: string;
  /** Label text for the select element */
  label: string;
  /** Array of options to display in the select */
  options: Array<{ value: string; label: string; disabled?: boolean }>;
  /** Additional CSS class name for the select element */
  className?: string;
  /** Additional CSS class name for the wrapper div */
  wrapperClassName?: string;
  /** Additional CSS class name for the label */
  labelClassName?: string;
  /** Error message to display below the select */
  error?: string;
  /** Help text to display below the select */
  helpText?: string;
  /** Whether the select is required */
  required?: boolean;
  'aria-invalid'?: boolean | 'false' | 'true' | 'grammar' | 'spelling';
  'aria-required'?: boolean | 'false' | 'true';
  'aria-describedby'?: string;
}

interface SelectContentProps {
  children: React.ReactNode;
  className?: string;
}

interface SelectItemProps extends React.OptionHTMLAttributes<HTMLOptionElement> {
  value: string;
  children: React.ReactNode;
  className?: string;
}

interface SelectTriggerProps {
  className?: string;
  children: React.ReactNode;
  id?: string;
  'aria-labelledby'?: string;
  'aria-label'?: string;
  'aria-describedby'?: string;
}

interface SelectValueProps {
  placeholder?: string;
  className?: string;
}

export const Select: React.FC<SelectProps> = ({
  id,
  label,
  options,
  className = '',
  wrapperClassName = '',
  labelClassName = '',
  error,
  helpText,
  required = false,
  ...props
}) => {
  const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;
  const errorId = error ? `${selectId}-error` : undefined;
  const helpTextId = helpText ? `${selectId}-help` : undefined;
  const ariaDescribedBy = [errorId, helpTextId].filter(Boolean).join(' ');

  return (
    <div className={`${styles.selectWrapper} ${wrapperClassName}`}>
      <div className={styles.labelContainer}>
        <label 
          id={`${selectId}-label`}
          htmlFor={selectId} 
          className={`${styles.label} ${labelClassName}`}
        >
          {label}
          {required && <span className={styles.requiredIndicator} aria-hidden="true">*</span>}
        </label>
        {helpText && (
          <span id={`${selectId}-help`} className={styles.helpText}>
            {helpText}
          </span>
        )}
      </div>
      
      <div className={styles.selectContainer}>
        <select
          id={selectId}
          className={`${styles.select} ${error ? styles.error : ''} ${className}`}
          aria-invalid={error ? 'true' : undefined}
          aria-required={required ? 'true' : undefined}
          aria-describedby={ariaDescribedBy || undefined}
          aria-labelledby={`${selectId}-label`}
          title={label}
          {...props}
        >
        {options.map((option) => (
          <option 
            key={option.value} 
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </option>
        ))}
        </select>
      </div>

      {error && (
        <p id={errorId} className={styles.errorMessage}>
          {error}
        </p>
      )}
      
      {helpText && !error && (
        <p id={helpTextId} className={styles.helpText}>
          {helpText}
        </p>
      )}
    </div>
  );
};

export const SelectContent: React.FC<SelectContentProps> = ({ children, className = '' }) => {
  return (
    <div className={`${styles.selectContent} ${className}`}>
      {children}
    </div>
  );
};

export const SelectItem: React.FC<SelectItemProps> = ({ 
  value, 
  children, 
  className = '',
  ...props 
}) => {
  return (
    <option 
      value={value} 
      className={`${styles.selectItem} ${className}`}
      {...props}
    >
      {children}
    </option>
  );
};

export const SelectTrigger: React.FC<SelectTriggerProps> = ({ 
  children, 
  className = '',
  ...props 
}) => {
  return (
    <div 
      className={`${styles.selectTrigger} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const SelectValue: React.FC<SelectValueProps> = ({ 
  placeholder = 'Select an option',
  className = '' 
}) => {
  return (
    <span className={`${styles.selectValue} ${className}`}>
      {placeholder}
    </span>
  );
};

export default Select;
