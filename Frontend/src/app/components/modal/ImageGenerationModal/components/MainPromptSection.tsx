/**
 * Main Prompt Section Component
 * Textarea for main transformation description
 */

import { MAX_MAIN_PROMPT_LENGTH } from '../utils/constants';
import styles from '../ImageGenerationModal.module.css';

interface MainPromptSectionProps {
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
}

export function MainPromptSection({ value, onChange, disabled }: MainPromptSectionProps) {
  return (
    <div className={styles.section}>
      <textarea
        id="mainPrompt"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Overall transformation description (e.g., 'Create a cyberpunk art style')..."
        className={styles.textarea}
        rows={2}
        disabled={disabled}
      />
      <div className={styles.characterCount}>
        {value.length}/{MAX_MAIN_PROMPT_LENGTH} characters
        {value.length > MAX_MAIN_PROMPT_LENGTH && (
          <span className={styles.warning}> (exceeds recommended limit)</span>
        )}
      </div>
    </div>
  );
}
