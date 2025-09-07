'use client';

import { useState } from 'react';
import { SettingsModalConfig } from './types';
import styles from './Modal.module.css';

interface SettingsModalProps {
  config: SettingsModalConfig;
}

export default function SettingsModal({ config }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState(config.defaultTab || config.tabs[0]?.id);

  const handleSave = () => {
    if (config.onSave) {
      config.onSave({});
    }
  };

  const handleReset = () => {
    if (config.onReset) {
      config.onReset();
    }
  };

  const activeTabContent = config.tabs.find(tab => tab.id === activeTab);

  return (
    <div className={styles.modalContent}>
      <div className={styles.settingsHeader}>
        <h2 className={styles.settingsTitle}>{config.title}</h2>
      </div>
      
      {config.tabs.length > 1 && (
        <div className={styles.tabsContainer}>
          {config.tabs.map(tab => (
            <button
              key={tab.id}
              className={`${styles.tabButton} ${activeTab === tab.id ? styles.activeTab : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}
      
      <div className={styles.settingsBody}>
        {activeTabContent?.component}
      </div>
      
      <div className={styles.modalFooter}>
        {config.onReset && (
          <button 
            className={`${styles.button} ${styles.tertiaryButton}`}
            onClick={handleReset}
          >
            Reset
          </button>
        )}
        <div className={styles.footerActions}>
          <button 
            className={`${styles.button} ${styles.secondaryButton}`}
            onClick={config.onClose}
          >
            Cancel
          </button>
          <button 
            className={`${styles.button} ${styles.primaryButton}`}
            onClick={handleSave}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}