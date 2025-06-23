import React, { useMemo } from 'react';
import styles from './Progress.module.css';

interface ProgressProps {
  /**
   * Current progress value (0 to max)
   */
  value: number;
  /**
   * Maximum progress value (default: 100)
   */
  max?: number;
  /**
   * Accessible label for the progress bar
   */
  label: string;
  /**
   * Additional CSS class for the container
   */
  className?: string;
  /**
   * Additional CSS class for the progress indicator
   */
  indicatorClassName?: string;
  /**
   * Description for screen readers
   */
  description?: string;
  /**
   * Show/hide the percentage text (default: false)
   */
  showPercentage?: boolean;
}

/**
 * An accessible progress bar component that shows the progress of a task.
 * 
 * @component
 * @example
 * ```tsx
 * <Progress 
 *   value={75} 
 *   max={100} 
 *   label="Upload progress"
 *   description="Uploading file..."
 *   showPercentage
 * />
 * ```
 */
export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  label,
  description,
  className = '',
  indicatorClassName = '',
  showPercentage = false,
}) => {
  const percentage = useMemo(() => 
    Math.min(Math.max((value / max) * 100, 0), 100), 
    [value, max]
  );

  const ariaValueNow = Math.round(value);
  const ariaValueText = `${ariaValueNow}%`;
  const progressId = React.useId();
  const descriptionId = description ? `progress-desc-${progressId}` : undefined;

  return (
    <div className={`${styles.progressContainer} ${className}`}>
      <div className={styles.progressHeader}>
        {label && (
          <span className={styles.progressLabel} id={`${progressId}-label`}>
            {label}
          </span>
        )}
        {showPercentage && (
          <span className={styles.percentage}>
            {ariaValueText}
          </span>
        )}
      </div>
      
      <div
        className={styles.progressBar}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={ariaValueNow}
        aria-valuetext={ariaValueText}
        aria-labelledby={`${progressId}-label`}
        aria-describedby={descriptionId}
        tabIndex={0}
      >
        <div
          className={`${styles.progressIndicator} ${indicatorClassName}`}
          style={{ '--progress-width': `${percentage}%` } as React.CSSProperties}
        />
      </div>
      
      {description && (
        <div id={descriptionId} className={styles.progressDescription}>
          {description}
        </div>
      )}
    </div>
  );
};

export default Progress;
