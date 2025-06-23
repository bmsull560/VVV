import React from 'react';
import styles from './Progress.module.css';

interface ProgressProps {
  value: number;
  max?: number;
  label?: string;
  className?: string;
  indicatorClassName?: string;
}

export const Progress: React.FC<ProgressProps> = ({ 
  value, 
  max = 100, 
  label = 'Progress',
  className = '', 
  indicatorClassName = '' 
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const ariaValueNow = Math.round(value);
  const ariaValueText = `${ariaValueNow}%`;

  return (
    <div className={`${styles.progressContainer} ${className}`}>
      {label && <span className="sr-only">{label}</span>}
      <div
        className={`${styles.progressBar} ${className}`}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={ariaValueNow}
        aria-valuetext={ariaValueText}
        aria-label={label}
      >
        <div
          className={`${styles.progressIndicator} ${indicatorClassName}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export default Progress;
