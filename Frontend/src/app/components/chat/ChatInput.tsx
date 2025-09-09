"use client";

import { useState, useEffect, useRef, forwardRef, useImperativeHandle, useMemo } from "react";
import { createApiService } from "../../services";
import { ApiKeyStatus } from "../../services/types";
import styles from "./ChatInput.module.css";

interface ChatInputProps {
	loading: boolean;
	error: string | null;
	sessionId: string | null;
	llmFromDb: 'gemini' | 'gemini-2' | 'claude';
	onSubmit: (prompt: string, model?: string) => Promise<unknown>;
	onRefreshContext: () => void;
}

export interface ChatInputHandle {
	focusInput: () => void;
}

const ChatInput = forwardRef<ChatInputHandle, ChatInputProps>(({
	loading,
	error,
	sessionId,
	llmFromDb,
	onSubmit,
	onRefreshContext,
}, ref) => {
	const [prompt, setPrompt] = useState("");
	const [submitting, setSubmitting] = useState(false);
	const [selectedLlm, setSelectedLlm] = useState<'gemini' | 'gemini-2' | 'claude'>(llmFromDb);
	const [showExamples, setShowExamples] = useState(false);
	const [apiKeyStatus, setApiKeyStatus] = useState<ApiKeyStatus | null>(null);
	const textareaRef = useRef<HTMLTextAreaElement>(null);

	const apiService = useMemo(() => createApiService(), []);

	// Expose focusInput method to parent
	useImperativeHandle(ref, () => ({
		focusInput: () => {
			textareaRef.current?.focus();
		}
	}));

	useEffect(() => {
		setSelectedLlm(llmFromDb);
	}, [llmFromDb]);

	// Check API key status on mount
	useEffect(() => {
		const checkApiKeys = async () => {
			try {
				const status = await apiService.getApiKeyStatus();
				setApiKeyStatus(status);
				
				// If current selected model is not available, switch to available one
				if (selectedLlm === 'claude' && !status.anthropic_available) {
					if (status.google_available) {
						setSelectedLlm('gemini');
					}
				} else if ((selectedLlm === 'gemini' || selectedLlm === 'gemini-2') && !status.google_available) {
					if (status.anthropic_available) {
						setSelectedLlm('claude');
					}
				}
			} catch (error) {
				console.error('Failed to check API key status:', error);
			}
		};

		checkApiKeys();
	}, [apiService, selectedLlm]);

	// Auto-resize textarea
	useEffect(() => {
		if (textareaRef.current) {
			textareaRef.current.style.height = 'auto';
			textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
		}
	}, [prompt]);

	const handleSubmit = async (e?: React.FormEvent) => {
		if (e) e.preventDefault();
		if (!prompt.trim() || isProcessing) return;

		setSubmitting(true);
		setShowExamples(false);

		try {
			const data = await onSubmit(prompt, selectedLlm);
			console.log("AI Response:", data);
			onRefreshContext();
			setPrompt("");
		} catch (err) {
			console.error('Submit failed:', err);
		} finally {
			setSubmitting(false);
			// Keep focus on textarea after command execution
			if (textareaRef.current) {
				textareaRef.current.focus();
			}
		}
	};

	const handleKeyDown = (e: React.KeyboardEvent) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
	};

	const handleExampleClick = (example: string) => {
		setPrompt(example);
		if (textareaRef.current) {
			textareaRef.current.focus();
		}
	};

	const isProcessing = loading || submitting;
	const canSubmit = prompt.trim() && !isProcessing;
	
	// Re-focus after loading finishes
	useEffect(() => {
		if (!isProcessing && sessionId) {
			const timer = setTimeout(() => {
				textareaRef.current?.focus();
			}, 50);
			return () => clearTimeout(timer);
		}
	}, [isProcessing, sessionId]);
	
	// Dynamic placeholder based on whether we have a session
	const placeholderText = sessionId 
		? "Message Unreal Engine..." 
		: "Enter session name to get started...";

	const examplePrompts = [
		"Set the time to sunrise (6 AM)",
		"Show me all actors in the current level", 
		"Set the sky to sunset time",
		"Set to San Francisco",
		"Move the map to Tokyo Japan",
		"Create a bright white light at position 0,0,200",
		"Create a warm orange light named MainLight",
		"Show me all MM control lights",
		"Take a high-resolution screenshot",
		"Make it rain and take a screenshot",
		"Take a screenshot and make it cyberpunk style",
		"Apply watercolor effect to last screenshot",
		"Transform image to Japan punk style",
		"Make the screenshot look like an anime",
	];

	return (
		<div className={styles.chatContainer}>
			{/* Main input area */}
			<div className={styles.inputContainer}>
				<div className={styles.inputWrapper}>
					<div className={styles.textareaRow}>
						<textarea
							ref={textareaRef}
							value={prompt}
							onChange={(e) => setPrompt(e.target.value)}
							onKeyDown={handleKeyDown}
							placeholder={prompt ? "" : placeholderText}
							className={styles.messageInput}
							rows={1}
							disabled={isProcessing}
						/>
						
						{/* Send button */}
						<button
							onClick={() => handleSubmit()}
							disabled={!canSubmit}
							className={`${styles.sendButton} ${canSubmit ? styles.sendButtonActive : ''}`}
							type="button"
						>
							{isProcessing ? (
								<div className={styles.spinner} />
							) : (
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<path
										d="M8 1L15 8L8 15M15 8H1"
										stroke="currentColor"
										strokeWidth="2"
										strokeLinecap="round"
										strokeLinejoin="round"
									/>
								</svg>
							)}
						</button>
					</div>
					
					{/* Bottom controls - Examples toggle and Model selector */}
					<div className={styles.bottomControls}>
						<button
							onClick={() => setShowExamples(!showExamples)}
							className={styles.examplesToggle}
							disabled={isProcessing}
						>
							{showExamples ? 'Hide examples' : 'Show examples'}
						</button>
						
						<select
							value={selectedLlm}
							onChange={(e) => setSelectedLlm(e.target.value as 'gemini' | 'gemini-2' | 'claude')}
							className={styles.modelSelect}
							disabled={isProcessing}
							title={apiKeyStatus ? 'Select AI model' : 'Checking API key availability...'}
						>
							<option 
								value="gemini" 
								disabled={apiKeyStatus !== null && !apiKeyStatus.google_available}
							>
								Gemini 1.5 Flash {apiKeyStatus && !apiKeyStatus.google_available ? '(API Key Missing)' : ''}
							</option>
							<option 
								value="gemini-2" 
								disabled={apiKeyStatus !== null && !apiKeyStatus.google_available}
							>
								Gemini 2.5 Flash {apiKeyStatus && !apiKeyStatus.google_available ? '(API Key Missing)' : ''}
							</option>
							<option 
								value="claude" 
								disabled={apiKeyStatus !== null && !apiKeyStatus.anthropic_available}
							>
								Claude 3 Haiku {apiKeyStatus && !apiKeyStatus.anthropic_available ? '(API Key Missing)' : ''}
							</option>
						</select>
					</div>
					
					{/* Examples */}
					{showExamples && (
						<div className={styles.examplesGrid}>
							{examplePrompts.map((example, index) => (
								<button
									key={index}
									onClick={() => handleExampleClick(example)}
									className={styles.exampleCard}
									disabled={isProcessing}
								>
									{example}
								</button>
							))}
						</div>
					)}
				</div>
			</div>

			{/* Error display */}
			{error && (
				<div className={styles.errorMessage}>
					{error}
				</div>
			)}
		</div>
	);
});

ChatInput.displayName = 'ChatInput';

export default ChatInput;
