'use client';

import styles from './MessageItem.module.css';

interface Object3DResult {
  fbx_uid?: string;
  obj_uid?: string;
  username?: string;
  user_id?: number;
  folder_path?: string;
  avatar_type?: string;
}

interface MessageItem3DResultProps {
  result: { command: string; success: boolean; result?: unknown; error?: string };
  resultIndex: number;
}

export default function MessageItem3DResult({
  result,
  resultIndex
}: MessageItem3DResultProps) {
  const data = (result.result ?? {}) as Object3DResult;

  // Extract 3D object data
  const objectUid = data.fbx_uid || data.obj_uid;
  const format = data.fbx_uid ? 'fbx' : data.obj_uid ? 'obj' : null;

  if (!objectUid) {
    return null;
  }

  const handleOpenFolder = async () => {
    if (!data.folder_path) {
      console.error('No folder path available');
      alert('Folder path not available');
      return;
    }

    try {
      const response = await fetch('/api/open-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: data.folder_path })
      });

      const result = await response.json();

      if (!response.ok) {
        console.error('Failed to open folder:', result);
        alert(`Failed to open folder: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error opening folder:', error);
      alert(`Error opening folder: ${error}`);
    }
  };

  return (
    <div className={styles.object3DContainer}>
      <div className={styles.object3DCard}>
        <div className={styles.object3DIcon}>
          {format === 'fbx' && '📦'}
          {format === 'obj' && '🔷'}
        </div>

        <div className={styles.object3DInfo}>
          <div className={styles.object3DTitle}>
            {data.username && data.user_id && data.avatar_type
              ? `${data.username}_${data.user_id}_${data.avatar_type}`
              : data.username || objectUid || 'Untitled Model'}
            <span className={styles.object3DFormat}>
              .{format || 'fbx'}
            </span>
          </div>
        </div>

        <div className={styles.object3DActions}>
          <button
            className={styles.downloadButton}
            onClick={handleOpenFolder}
            title="Open folder location"
          >
            📂 Open Folder
          </button>
        </div>
      </div>
    </div>
  );
}
