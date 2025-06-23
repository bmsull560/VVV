import React from 'react';
import styles from './Switch.module.css';

interface SwitchProps {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  className?: string;
  disabled?: boolean;
  label: string;
  id: string;
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
        disabled={disabled}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        className={`${styles.switch} ${checked ? styles.checked : ''} ${disabled ? styles.disabled : ''}`}
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
