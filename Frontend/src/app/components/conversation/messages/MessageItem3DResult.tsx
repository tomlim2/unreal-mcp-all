'use client';

import { useState } from 'react';
import styles from './MessageItem.module.css';

interface Object3DResult {
  object_3d?: {
    uid?: string;
    url?: string;
    format?: string;
    file_size?: number;
    vertices?: number;
    faces?: number;
  };
  fbx_uid?: string;
  obj_uid?: string;
}

interface MessageItem3DResultProps {
  result: Object3DResult;
  resultIndex: number;
}

export default function MessageItem3DResult({
  result,
  resultIndex
}: MessageItem3DResultProps) {
  const [showPreview, setShowPreview] = useState(false);

  // Check for 3D object in new format
  const object3D = result.object_3d;
  const objectUid = object3D?.uid || result.fbx_uid || result.obj_uid;
  const objectUrl = object3D?.url ||
                    (objectUid ? `/api/3d-object/${objectUid}` : null);
  const format = object3D?.format ||
                 (result.fbx_uid ? 'fbx' : null) ||
                 (result.obj_uid ? 'obj' : null);

  if (!objectUrl && !objectUid) {
    return null;
  }

  const handleDownload = () => {
    if (objectUrl) {
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = `${objectUid || 'model'}.${format || 'fbx'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size';
    const mb = bytes / (1024 * 1024);
    return mb < 1
      ? `${(bytes / 1024).toFixed(1)} KB`
      : `${mb.toFixed(2)} MB`;
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
            {objectUid || 'Untitled Model'}
            <span className={styles.object3DFormat}>
              .{format || 'fbx'}
            </span>
          </div>

          <div className={styles.object3DDetails}>
            {object3D?.file_size && (
              <span>{formatFileSize(object3D.file_size)}</span>
            )}
            {object3D?.vertices && (
              <span>• {object3D.vertices.toLocaleString()} vertices</span>
            )}
            {object3D?.faces && (
              <span>• {object3D.faces.toLocaleString()} faces</span>
            )}
          </div>
        </div>

        <div className={styles.object3DActions}>
          <button
            className={styles.downloadButton}
            onClick={handleDownload}
            title="Download 3D object"
          >
            ⬇️ Download
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
