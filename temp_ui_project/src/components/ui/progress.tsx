import React, { useMemo, HTMLAttributes } from 'react';
import styles from './Progress.module.css';

// Extend HTMLAttributes to include our custom ARIA attributes
interface ProgressBarProps extends Omit<HTMLAttributes<HTMLDivElement>, 'role'> {
  'aria-valuemin'?: number;
  'aria-valuemax'?: number;
  'aria-valuenow'?: number;
  'aria-valuetext'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  role?: 'progressbar';
}

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

  // Generate unique IDs for ARIA attributes
  const labelId = `${progressId}-label`;
  
  // Generate a class name for the current percentage
  const indicatorClass = `${styles.progressIndicator} ${styles[`width_${Math.round(percentage)}`] || ''}`;

  // Create the progress bar props with proper typing
  const progressBarProps: ProgressBarProps = {
    className: `${styles.progressBar} ${indicatorClassName}`,
    role: 'progressbar',
    'aria-valuemin': 0,
    'aria-valuemax': max,
    'aria-valuenow': ariaValueNow,
    'aria-valuetext': ariaValueText,
    'aria-labelledby': labelId,
    'aria-describedby': descriptionId,
    tabIndex: 0,
  };

  return (
    <div className={`${styles.progressContainer} ${className}`}>
      <div className={styles.progressHeader}>
        {label && (
          <span id={labelId} className={styles.progressLabel}>
            {label}
          </span>
        )}
        {showPercentage && (
          <span className={styles.percentage}>
            {ariaValueText}
          </span>
        )}
      </div>
      
      <div {...progressBarProps}>
        <div
          className={indicatorClass}
          aria-hidden="true"
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
