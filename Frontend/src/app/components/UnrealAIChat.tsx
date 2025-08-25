'use client';

import { useState } from 'react';
import styles from './UnrealAIChat.module.css';

interface CommandResult {
  command: string;
  success: boolean;
  result?: any;
  error?: string;
}

interface AIResponse {
  explanation?: string;
  commands?: Array<{
    type: string;
    params: Record<string, any>;
  }>;
  expectedResult?: string;
  executionResults?: CommandResult[];
  error?: string;
  fallback?: boolean;
}

export default function UnrealLlmChat() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AIResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await fetch('/api/mcp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          context: 'User is working with Unreal Engine project with dynamic sky system'
        }),
      });

      if (!res.ok) {
        throw new Error('Failed to get AI response');
      }

      const data: AIResponse = await res.json();
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleExamplePrompt = (examplePrompt: string) => {
    setPrompt(examplePrompt);
  };

  const examplePrompts = [
    "Set the time to sunrise (6 AM)",
    "Create a cube actor at position 0,0,100",
    "Show me all actors in the current level",
    "Set the sky to sunset time",
    "Delete the actor named 'TestCube'",
    "Move the camera to position 500,0,200",
    "Set to San Francisco",
    "Set the New York City",
    "Move the map to Tokyo Japan"
  ];

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Unreal Engine MCP Frontend</h2>
      <p className={styles.subtitle}>
        Powered by Python MCP Server with Claude-3-Haiku
      </p>
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.inputGroup}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!loading && prompt.trim()) {
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
            disabled={loading || !prompt.trim()}
            className={styles.submitButton}
          >
            {loading ? 'Processing...' : 'Execute'}
          </button>
        </div>
      </form>
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

      {response && (
        <div className={styles.response}>
          {response.error && (
            <div className={styles.error}>
              <h3>❌ Server Error</h3>
              <p>{response.error}</p>
              {response.fallback && (
                <p><em>This is a fallback response - check if all services are running.</em></p>
              )}
            </div>
          )}
          
          {response.explanation && (
            <div className={styles.explanation}>
              <h3>LLM Output</h3>
              <p>{response.explanation}</p>
            </div>
          )}

          {response.commands && response.commands.length > 0 && (
            <div className={styles.commands}>
              <h3>Generated Commands</h3>
              {response.commands.map((cmd, index) => (
                <div key={index} className={styles.command}>
                  <strong>{cmd.type}</strong>
                  <pre>{JSON.stringify(cmd.params, null, 2)}</pre>
                </div>
              ))}
            </div>
          )}

          {response.executionResults && response.executionResults.length > 0 && (
            <div className={styles.results}>
              <h3>Execution Results</h3>
              {response.executionResults.map((result, index) => (
                <div
                  key={index}
                  className={`${styles.result} ${
                    result.success ? styles.success : styles.failure
                  }`}
                >
                  <div className={styles.resultHeader}>
                    <span className={styles.commandName}>{result.command}</span>
                    <span className={styles.status}>
                      {result.success ? '✅' : '❌'}
                    </span>
                  </div>
                  {result.success ? (
                    <pre className={styles.resultData}>
                      {JSON.stringify(result.result, null, 2)}
                    </pre>
                  ) : (
                    <p className={styles.errorMessage}>{result.error}</p>
                  )}
                </div>
              ))}
            </div>
          )}

          {response.expectedResult && (
            <div className={styles.expected}>
              <h3>🎯 Expected Result</h3>
              <p>{response.expectedResult}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}