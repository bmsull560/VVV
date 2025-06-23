import React from 'react';
import styles from './Select.module.css';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'aria-invalid' | 'aria-required' | 'aria-describedby'> {
  id: string;
  label: string;
  options: SelectOption[];
  className?: string;
  wrapperClassName?: string;
  labelClassName?: string;
  error?: string;
  helpText?: string;
  required?: boolean;
  'aria-invalid'?: boolean | 'true' | 'false';
  'aria-required'?: boolean | 'true' | 'false';
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
      <label 
        htmlFor={selectId} 
        className={`${styles.label} ${labelClassName}`}
      >
        {label}
        {required && <span className={styles.requiredIndicator} aria-hidden="true">*</span>}
      </label>
      
      <select
        id={selectId}
        className={`${styles.select} ${error ? styles.error : ''} ${className}`}
        aria-invalid={error ? 'true' : 'false'}
        aria-required={required ? 'true' : 'false'}
        aria-describedby={ariaDescribedBy || undefined}
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
