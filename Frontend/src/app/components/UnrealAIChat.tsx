"use client";

import { useState, useEffect } from "react";
import styles from "./UnrealAIChat.module.css";

interface UnrealLlmChatProps {
  loading: boolean;
  error: string | null;
  sessionId: string | null;
  llmFromDb: 'gemini' | 'gemini-2' | 'claude';
  onSubmit: (prompt: string, context: string, model?: string) => Promise<unknown>;
  onRefreshContext: () => void;
}

export default function UnrealLlmChat({
  loading,
  error,
  sessionId,
  llmFromDb,
  onSubmit,
  onRefreshContext,
}: UnrealLlmChatProps) {
  const [prompt, setPrompt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [selectedLlm, setSelectedLlm] = useState<'gemini' | 'gemini-2' | 'claude'>(llmFromDb);
  useEffect(() => {
    setSelectedLlm(llmFromDb);
  }, [llmFromDb]);
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setSubmitting(true);

    try {
      const data = await onSubmit(
        prompt,
        "User is a creative cinema director",
        selectedLlm
      );

      console.log("AI Response:", data);
      onRefreshContext();
      setPrompt(""); // Clear the input after successful submission
    } catch (err) {
      // Error is handled by parent component
      console.error('Submit failed:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleExamplePrompt = (examplePrompt: string) => {
    setPrompt(examplePrompt);
  };

  const examplePrompts = [
    "Set the time to sunrise (6 AM)",
    "Show me all actors in the current level",
    "Set the sky to sunset time",
    "Set to San Francisco",
    "Set the New York City",
    "Move the map to Tokyo Japan",
    "Create a bright white light at position 0,0,200",
    "Create a warm orange light named MainLight",
    "Show me all MM control lights",
    "Make MainLight red and move it to 100,100,150",
    "Delete the light named MainLight",
  ];

  return (
    <>
      <div className={styles.container}>
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.inputGroup}>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  if (!loading && !submitting && prompt.trim()) {
                    const form = e.currentTarget.form;
                    if (form) {
                      form.requestSubmit();
                    }
                  }
                }
              }}
              placeholder="Describe what you want to do in Unreal Engine... (Press Enter to execute, Shift+Enter for new line)"
              className={styles.textarea}
              rows={3}
            />
            <button
              type="submit"
              disabled={loading || submitting || !prompt.trim()}
              className={styles.submitButton}
            >
              {loading || submitting ? "Processing..." : "Execute"}
            </button>
          </div>
        </form>
		<div className={styles.modelSwitcher}>
        <label htmlFor="model-select" className={styles.modelLabel}>
          AI Model: {sessionId && `(Session: ${sessionId.slice(-8)})`}
        </label>
        <select
          id="model-select"
          value={selectedLlm}
          onChange={(e) => setSelectedLlm(e.target.value as 'gemini' | 'gemini-2' | 'claude')}
          className={styles.modelSelect}
          disabled={loading || submitting}
        >
			<option value="gemini">gemini-1.5-flash</option>
            <option value="gemini-2">gemini-2.5-flash</option>
            <option value="claude">claude-3-haiku-20240307</option>
        </select>
      </div>
      </div>
      <div className={styles.examples}>
        <h3>Examples:</h3>
        <div className={styles.exampleButtons}>
          {examplePrompts.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExamplePrompt(example)}
              className={styles.exampleButton}
            >
              {example}
            </button>
          ))}
        </div>
      </div>
      {error && (
        <div className={styles.error}>
          <h3>❌ Error</h3>
          <p>{error}</p>
        </div>
      )}

      {(loading || submitting) && (
        <div className={styles.loading}>
          <p>Processing your request...</p>
        </div>
      )}
    </>
  );
}
