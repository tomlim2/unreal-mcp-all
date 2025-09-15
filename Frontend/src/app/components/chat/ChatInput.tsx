"use client";

import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from "react";
import styles from "./ChatInput.module.css";

interface ChatInputProps {
	loading: boolean;
	error: string | null;
	sessionId: string | null;
	llmFromDb: 'gemini' | 'gemini-2' | 'claude';
	onSubmit: (prompt: string, model?: string) => Promise<unknown>;
	onRefreshContext: () => void;
	allowModelSwitching?: boolean; // New prop to control model switcher
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
	allowModelSwitching = true, // Default to true for backward compatibility
}, ref) => {
	const [prompt, setPrompt] = useState("");
	const [submitting, setSubmitting] = useState(false);
	const [selectedLlm, setSelectedLlm] = useState<'gemini' | 'gemini-2' | 'claude'>(llmFromDb);
	const [showExamples, setShowExamples] = useState(false);
	const textareaRef = useRef<HTMLTextAreaElement>(null);

	// Expose focusInput method to parent
	useImperativeHandle(ref, () => ({
		focusInput: () => {
			textareaRef.current?.focus();
		}
	}));

	useEffect(() => {
		setSelectedLlm(llmFromDb);
	}, [llmFromDb]);

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

	const handleScreenshotClick = async () => {
		if (isProcessing) return;
		
		setSubmitting(true);
		setShowExamples(false);

		try {
			const data = await onSubmit("Take a screenshot", selectedLlm);
			console.log("Screenshot Response:", data);
			onRefreshContext();
		} catch (err) {
			console.error('Screenshot failed:', err);
		} finally {
			setSubmitting(false);
			// Keep focus on textarea after command execution
			if (textareaRef.current) {
				textareaRef.current.focus();
			}
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
						
						{/* Screenshot button */}
						<button
							onClick={handleScreenshotClick}
							disabled={isProcessing}
							className={`${styles.screenshotButton} ${!isProcessing ? styles.screenshotButtonActive : ''}`}
							type="button"
							title="Take Screenshot"
						>
							{isProcessing ? (
								<div className={styles.spinner} />
							) : (
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none">
									<path
										d="M9 2L7.17 4H4C2.9 4 2 4.9 2 6V18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V6C22 4.9 21.1 4 20 4H16.83L15 2H9ZM12 17C9.24 17 7 14.76 7 12S9.24 7 12 7S17 9.24 17 12S14.76 17 12 17ZM12 9C10.34 9 9 10.34 9 12S10.34 15 12 15S15 13.66 15 12S13.66 9 12 9Z"
										fill="currentColor"
									/>
								</svg>
							)}
						</button>

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
							onChange={(e) => allowModelSwitching && setSelectedLlm(e.target.value as 'gemini' | 'gemini-2' | 'claude')}
							className={`${styles.modelSelect} ${!allowModelSwitching ? styles.modelSelectDisabled : ''}`}
							disabled={isProcessing || !allowModelSwitching}
						>
							<option value="gemini">Gemini 1.5 Flash</option>
							<option value="gemini-2">Gemini 2.5 Flash</option>
							<option value="claude">Claude 3 Haiku</option>
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
