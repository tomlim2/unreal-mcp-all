"use client";

import { useState } from "react";
import styles from "./UnrealAIChat.module.css";

interface UnrealLlmChatProps {
  loading: boolean;
  error: string | null;
  sessionId: string | null;
  onSubmit: (prompt: string, context: string) => Promise<unknown>;
  onRefreshContext: () => void;
}

export default function UnrealLlmChat({
  loading,
  error,
  sessionId,
  onSubmit,
  onRefreshContext,
}: UnrealLlmChatProps) {
  const [prompt, setPrompt] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setSubmitting(true);

    try {
      console.log("Session ID:", sessionId);
      const data = await onSubmit(
        prompt,
        "User is working with Unreal Engine project with dynamic sky system"
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
