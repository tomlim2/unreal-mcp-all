'use client';

import { useState } from 'react';
import styles from './MessageItem.module.css';

interface Object3DResult {
  fbx_uid?: string;
  obj_uid?: string;
  username?: string;
  user_id?: number;
  folder_path?: string;
  avatar_type?: string;
  file_paths?: {
    folder?: string;
  };
}

interface MessageItem3DResultProps {
  result: { command: string; success: boolean; result?: unknown; error?: string };
  resultIndex: number;
}

export default function MessageItem3DResult({
  result,
  resultIndex
}: MessageItem3DResultProps) {
  const [showPreview, setShowPreview] = useState(false);
  const data = (result.result ?? {}) as Object3DResult;

  // Extract 3D object data from flat structure
  const objectUid = data.fbx_uid || data.obj_uid;
  const format = data.fbx_uid ? 'fbx' : data.obj_uid ? 'obj' : null;

  if (!objectUid) {
    return null;
  }

  const handleOpenFolder = async () => {
    // Check both flat structure (folder_path) and nested structure (file_paths.folder)
    const folderPath = data.folder_path || data.file_paths?.folder;

    if (folderPath) {
      try {
        const response = await fetch('/api/open-folder', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: folderPath })
        });
        if (!response.ok) {
          console.error('Failed to open folder');
        }
      } catch (error) {
        console.error('Error opening folder:', error);
      }
    }
  };

  return (
    <div className={styles.object3DContainer}>
      <div className={styles.object3DCard}>
        <div className={styles.object3DIcon}>
          {format === 'fbx' && '📦'}
          {format === 'obj' && '🔷'}
          {format === 'gltf' && '🎁'}
          {format === 'glb' && '🎁'}
          {!format && '🗿'}
        </div>

        <div className={styles.object3DInfo}>
          <div className={styles.object3DTitle}>
            {data.username || objectUid || 'Untitled Model'}
            {data.avatar_type && data.avatar_type !== 'Unknown' && (
              <span className={styles.object3DRigType}>
                {data.avatar_type}
              </span>
            )}
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
          {/* Future: Add 3D preview button */}
          {/* <button
            className={styles.previewButton}
            onClick={() => setShowPreview(!showPreview)}
            title="Preview 3D object"
          >
            👁️ {showPreview ? 'Hide' : 'Preview'}
          </button> */}
        </div>
      </div>

      {showPreview && (
        <div className={styles.object3DPreview}>
          <div className={styles.previewPlaceholder}>
            3D Preview (Coming Soon)
            <p>Use external viewer or import into Unreal/Blender</p>
          </div>
        </div>
      )}
    </div>
  );
}
