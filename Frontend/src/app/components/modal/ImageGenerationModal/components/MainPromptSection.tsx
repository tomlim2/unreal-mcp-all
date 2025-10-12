/**
 * Main Prompt Section Component
 * Textarea for main transformation description
 */

import { useRef, useEffect } from 'react';
import styles from '../ImageGenerationModal.module.css';

interface MainPromptSectionProps {
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
}

export function MainPromptSection({ value, onChange, disabled }: MainPromptSectionProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [value]);

  return (
    <div className={styles.section}>
      <textarea
        ref={textareaRef}
        id="mainPrompt"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Overall transformation description (e.g., 'Create a cyberpunk art style')..."
        className={styles.textarea}
        rows={2}
        disabled={disabled}
      />
    </div>
  );
}
