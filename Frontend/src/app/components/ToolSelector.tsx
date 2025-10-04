'use client';

import { useState, useEffect } from 'react';
import styles from './ToolSelector.module.css';

export interface Tool {
  tool_id: string;
  display_name: string;
  version: string;
  description: string;
  icon?: string;
  status: 'available' | 'unavailable' | 'error' | 'disabled';
  capabilities: string[];
}

interface ToolSelectorProps {
  selectedTool?: string;
  onToolSelect?: (toolId: string) => void;
  disabled?: boolean;
}

export default function ToolSelector({
  selectedTool,
  onToolSelect,
  disabled = false
}: ToolSelectorProps) {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    fetchTools();
  }, []);

  const fetchTools = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/tools');
      if (!response.ok) {
        throw new Error('Failed to fetch tools');
      }
      const data = await response.json();
      setTools(data.tools || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching tools:', err);
      setError('Failed to load tools');
      // Fallback to default tools
      setTools([
        {
          tool_id: 'unreal_engine',
          display_name: 'Unreal Engine',
          version: '5.5.4',
          description: 'Real-time 3D creation',
          icon: '🎮',
          status: 'available',
          capabilities: ['rendering', 'lighting', 'camera']
        },
        {
          tool_id: 'nano_banana',
          display_name: 'Nano Banana',
          version: '1.0.0',
          description: 'AI image generation & editing',
          icon: '🍌',
          status: 'available',
          capabilities: ['image_editing', 'style_transfer']
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleToolClick = (toolId: string) => {
    if (!disabled && onToolSelect) {
      onToolSelect(toolId);
      setIsOpen(false);
    }
  };

  const currentTool = tools.find(t => t.tool_id === selectedTool) || tools[0];

  if (loading) {
    return (
      <div className={styles.toolSelector}>
        <div className={styles.loading}>Loading tools...</div>
      </div>
    );
  }

  if (error && tools.length === 0) {
    return (
      <div className={styles.toolSelector}>
        <div className={styles.error}>{error}</div>
      </div>
    );
  }

  return (
    <div className={styles.toolSelector}>
      <button
        className={`${styles.selectedTool} ${disabled ? styles.disabled : ''}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
      >
        <span className={styles.toolIcon}>{currentTool?.icon || '🔧'}</span>
        <span className={styles.toolName}>{currentTool?.display_name || 'Select Tool'}</span>
        <span className={styles.arrow}>{isOpen ? '▲' : '▼'}</span>
      </button>

      {isOpen && !disabled && (
        <div className={styles.dropdown}>
          {tools.map(tool => (
            <button
              key={tool.tool_id}
              className={`${styles.toolOption} ${
                tool.tool_id === selectedTool ? styles.active : ''
              } ${tool.status !== 'available' ? styles.unavailable : ''}`}
              onClick={() => handleToolClick(tool.tool_id)}
              disabled={tool.status !== 'available'}
            >
              <div className={styles.toolHeader}>
                <span className={styles.toolIcon}>{tool.icon || '🔧'}</span>
                <div className={styles.toolInfo}>
                  <div className={styles.toolTitle}>
                    {tool.display_name}
                    <span className={styles.version}>v{tool.version}</span>
                  </div>
                  <div className={styles.toolDescription}>{tool.description}</div>
                </div>
                <span className={`${styles.status} ${styles[tool.status]}`}>
                  {tool.status === 'available' ? '●' : '○'}
                </span>
              </div>
              <div className={styles.capabilities}>
                {tool.capabilities.slice(0, 3).map(cap => (
                  <span key={cap} className={styles.capability}>
                    {cap.replace(/_/g, ' ')}
                  </span>
                ))}
                {tool.capabilities.length > 3 && (
                  <span className={styles.capability}>
                    +{tool.capabilities.length - 3} more
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
