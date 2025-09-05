'use client';

import MessageItem from './MessageItem';
import styles from './MessageGroup.module.css';

interface ChatMessage {
  timestamp: string;
  role: 'user' | 'assistant' | 'system' | 'job';
  content: string;
  commands?: Array<{
    type: string;
    params: Record<string, unknown>;
  }>;
  execution_results?: Array<{
    command: string;
    success: boolean;
    result?: Record<string, any> & {
      image_url?: string;
    };
    error?: string;
  }>;
  job_status?: 'pending' | 'running' | 'completed' | 'failed';
  job_progress?: number;
  image_url?: string;
}

interface MessageGroup {
  userMessage: ChatMessage;
  responses: ChatMessage[];
}

interface MessageGroupProps {
  messages: ChatMessage[];
  sessionId?: string;
}

function groupMessagesByUser(messages: ChatMessage[]): MessageGroup[] {
  const groups: MessageGroup[] = [];
  let currentGroup: MessageGroup | null = null;

  messages.forEach((message, index) => {
    if (message.role === 'user') {
      // Start a new group with this user message
      if (currentGroup) {
        groups.push(currentGroup);
      }
      currentGroup = {
        userMessage: message,
        responses: []
      };
    } else if (currentGroup) {
      // Add response to current group
      currentGroup.responses.push(message);
    } else {
      // Handle orphaned response messages (responses without a user message)
      // Create a synthetic user message group
      const syntheticUserMessage: ChatMessage = {
        timestamp: message.timestamp,
        role: 'user',
        content: '[Previous conversation]'
      };
      currentGroup = {
        userMessage: syntheticUserMessage,
        responses: [message]
      };
    }
  });

  // Don't forget the last group
  if (currentGroup) {
    groups.push(currentGroup);
  }

  return groups;
}

export default function MessageGroupWrapper({ messages, sessionId }: MessageGroupProps) {
  const messageGroups = groupMessagesByUser(messages);

  return (
    <div className={styles.messageGroupWrapper}>
      {messageGroups.map((group, groupIndex) => {
        return (
          <div key={groupIndex} className={styles.messageGroup}>
            {/* User Message - Always Visible */}
            <div className={styles.userMessageContainer}>
              <MessageItem
                message={group.userMessage}
                index={groupIndex * 100} // Use group index * 100 for user messages
                sessionId={sessionId}
              />
            </div>

            {/* Response Messages - Always Visible */}
            {group.responses.length > 0 && (
              <div className={styles.responsesContainer}>
                {group.responses.map((response, responseIndex) => (
                  <MessageItem
                    key={`${groupIndex}-${responseIndex}`}
                    message={response}
                    index={groupIndex * 100 + responseIndex + 1} // Nested indexing
                    sessionId={sessionId}
                    previousMessage={responseIndex > 0 ? group.responses[responseIndex - 1] : group.userMessage}
                  />
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}