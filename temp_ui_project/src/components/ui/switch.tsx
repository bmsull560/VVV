import React from 'react';
import styles from './Switch.module.css';

// Extend button props but exclude the ones we're customizing
type SwitchButtonProps = Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 
  'onChange' | 'onClick' | 'aria-checked' | 'aria-disabled' | 'role' | 'type'
> & {
  /**
   * The type of the button. Set to 'button' to prevent form submission.
   * @default 'button'
   */
  type?: 'button' | 'submit' | 'reset';
};

interface SwitchProps extends SwitchButtonProps {
  /**
   * The controlled checked state of the switch.
   * Must be used in conjunction with onCheckedChange.
   */
  checked?: boolean;
  
  /**
   * Event handler called when the checked state changes.
   */
  onCheckedChange?: (checked: boolean) => void;
  
  /** Additional class name for the container */
  className?: string;
  
  /** Whether the switch is disabled */
  disabled?: boolean;
  
  /** Label text for the switch */
  label: string;
  
  /** Unique identifier for the switch */
  id: string;
  
  /**
   * The value of the switch when used in a form.
   * @default 'on'
   */
  value?: string;
  
  /**
   * The name of the switch when used in a form.
   */
  name?: string;
}

export const Switch: React.FC<SwitchProps> = ({ 
  checked = false, 
  onCheckedChange, 
  className = '',
  disabled = false,
  label,
  id
}) => {
  const handleClick = () => {
    if (!disabled && onCheckedChange) {
      onCheckedChange(!checked);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <div className={`${styles.switchContainer} ${className}`}>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        aria-labelledby={`${id}-label`}
        aria-disabled={disabled}
        disabled={disabled}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        className={`${styles.switch} ${checked ? styles.checked : ''} ${disabled ? styles.disabled : ''}`}
        tabIndex={disabled ? -1 : 0}
        {...props}
      >
        <span className={styles.switchHandle} />
      </button>
      <label id={`${id}-label`} htmlFor={id} className={styles.switchLabel}>
        {label}
      </label>
    </div>
  );
};

export default Switch;
