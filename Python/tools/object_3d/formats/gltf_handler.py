"""
GLTF Format Handler for GLTF/GLB files.

Handles analysis and validation of GLTF 2.0 format files.
GLTF uses JSON structure which allows for better parsing than binary formats.
"""

import json
import struct
from pathlib import Path
from typing import Dict, Any, List, Tuple
from .base import BaseFormatHandler


class GLTFFormatHandler(BaseFormatHandler):
    """Handler for GLTF 2.0 format files (.gltf and .glb)."""

    def __init__(self):
        super().__init__("GLTF 2.0", ['.gltf', '.glb'])

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze GLTF file structure."""
        analysis = {
            'vertex_count': 0,
            'face_count': 0,
            'triangle_count': 0,
            'bounding_box': {"min": [0.0, 0.0, 0.0], "max": [0.0, 0.0, 0.0]},
            'has_normals': False,
            'has_texture_coords': False,
            'material_references': [],
            'groups': [],
            'format_specific': {
                'gltf_version': '2.0',
                'is_binary_glb': file_path.suffix.lower() == '.glb',
                'has_animation': False,
                'has_skeleton': False,
                'scene_count': 0,
                'node_count': 0,
                'mesh_count': 0,
                'material_count': 0,
                'texture_count': 0,
                'extensions_used': [],
                'extensions_required': []
            }
        }

        try:
            if analysis['format_specific']['is_binary_glb']:
                gltf_data = self._parse_glb_file(file_path)
            else:
                gltf_data = self._parse_gltf_file(file_path)

            if gltf_data:
                analysis = self._analyze_gltf_data(gltf_data, analysis)

        except Exception as e:
            self.logger.warning(f"Failed to analyze GLTF file {file_path}: {e}")
            analysis['analysis_error'] = str(e)

        return analysis

    def _parse_gltf_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse JSON GLTF file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _parse_glb_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse binary GLB file to extract JSON data."""
        with open(file_path, 'rb') as f:
            # GLB header: magic(4) + version(4) + length(4)
            header = f.read(12)
            if len(header) != 12:
                raise ValueError("Invalid GLB file: incomplete header")

            magic, version, length = struct.unpack('<III', header)

            if magic != 0x46546C67:  # 'glTF' in little-endian
                raise ValueError("Invalid GLB file: incorrect magic number")

            # First chunk should be JSON
            chunk_header = f.read(8)
            if len(chunk_header) != 8:
                raise ValueError("Invalid GLB file: incomplete chunk header")

            chunk_length, chunk_type = struct.unpack('<II', chunk_header)

            if chunk_type != 0x4E4F534A:  # 'JSON' in little-endian
                raise ValueError("Invalid GLB file: first chunk is not JSON")

            json_data = f.read(chunk_length)
            return json.loads(json_data.decode('utf-8'))

    def _analyze_gltf_data(self, gltf_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze parsed GLTF JSON data."""

        # Basic GLTF structure
        analysis['format_specific']['gltf_version'] = gltf_data.get('asset', {}).get('version', '2.0')

        # Extensions
        if 'extensionsUsed' in gltf_data:
            analysis['format_specific']['extensions_used'] = gltf_data['extensionsUsed']

        if 'extensionsRequired' in gltf_data:
            analysis['format_specific']['extensions_required'] = gltf_data['extensionsRequired']

        # Count various elements
        scenes = gltf_data.get('scenes', [])
        nodes = gltf_data.get('nodes', [])
        meshes = gltf_data.get('meshes', [])
        materials = gltf_data.get('materials', [])
        textures = gltf_data.get('textures', [])
        animations = gltf_data.get('animations', [])
        skins = gltf_data.get('skins', [])

        analysis['format_specific']['scene_count'] = len(scenes)
        analysis['format_specific']['node_count'] = len(nodes)
        analysis['format_specific']['mesh_count'] = len(meshes)
        analysis['format_specific']['material_count'] = len(materials)
        analysis['format_specific']['texture_count'] = len(textures)
        analysis['format_specific']['has_animation'] = len(animations) > 0
        analysis['format_specific']['has_skeleton'] = len(skins) > 0

        # Analyze meshes for geometry data
        accessors = gltf_data.get('accessors', [])
        total_vertices = 0
        total_triangles = 0
        has_normals = False
        has_texture_coords = False

        for mesh in meshes:
            mesh_name = mesh.get('name', f'mesh_{meshes.index(mesh)}')
            analysis['groups'].append(mesh_name)

            for primitive in mesh.get('primitives', []):
                attributes = primitive.get('attributes', {})

                # Count vertices from POSITION accessor
                if 'POSITION' in attributes:
                    position_accessor_idx = attributes['POSITION']
                    if position_accessor_idx < len(accessors):
                        position_accessor = accessors[position_accessor_idx]
                        vertex_count = position_accessor.get('count', 0)
                        total_vertices += vertex_count

                        # Update bounding box if available
                        if 'min' in position_accessor and 'max' in position_accessor:
                            pos_min = position_accessor['min']
                            pos_max = position_accessor['max']

                            if analysis['bounding_box']['min'] == [0.0, 0.0, 0.0] and analysis['bounding_box']['max'] == [0.0, 0.0, 0.0]:
                                analysis['bounding_box']['min'] = pos_min[:]
                                analysis['bounding_box']['max'] = pos_max[:]
                            else:
                                for i in range(3):
                                    analysis['bounding_box']['min'][i] = min(analysis['bounding_box']['min'][i], pos_min[i])
                                    analysis['bounding_box']['max'][i] = max(analysis['bounding_box']['max'][i], pos_max[i])

                # Check for normals
                if 'NORMAL' in attributes:
                    has_normals = True

                # Check for texture coordinates
                if 'TEXCOORD_0' in attributes:
                    has_texture_coords = True

                # Count triangles from indices
                indices_accessor_idx = primitive.get('indices')
                if indices_accessor_idx is not None and indices_accessor_idx < len(accessors):
                    indices_accessor = accessors[indices_accessor_idx]
                    index_count = indices_accessor.get('count', 0)

                    # Assume triangles (mode 4 is TRIANGLES in GLTF)
                    mode = primitive.get('mode', 4)
                    if mode == 4:  # TRIANGLES
                        total_triangles += index_count // 3

        analysis['vertex_count'] = total_vertices
        analysis['triangle_count'] = total_triangles
        analysis['face_count'] = total_triangles  # In GLTF, triangles are the primary primitive
        analysis['has_normals'] = has_normals
        analysis['has_texture_coords'] = has_texture_coords

        # Material references
        for material in materials:
            material_name = material.get('name', f'material_{materials.index(material)}')
            analysis['material_references'].append(material_name)

        return analysis

    def validate_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate GLTF file for format compliance and common issues."""
        issues = []

        try:
            if not file_path.exists():
                return False, ["File does not exist"]

            if file_path.stat().st_size == 0:
                return False, ["File is empty"]

            # Attempt to parse the file
            if file_path.suffix.lower() == '.glb':
                gltf_data = self._parse_glb_file(file_path)
            else:
                gltf_data = self._parse_gltf_file(file_path)

            # Validate required GLTF structure
            if 'asset' not in gltf_data:
                issues.append("Missing required 'asset' field in GLTF")

            asset = gltf_data.get('asset', {})
            version = asset.get('version')
            if not version:
                issues.append("Missing GLTF version in asset field")
            elif not version.startswith('2.'):
                issues.append(f"Unsupported GLTF version: {version} (expected 2.x)")

            # Validate required extensions
            extensions_required = gltf_data.get('extensionsRequired', [])
            if extensions_required:
                issues.append(f"File requires extensions that may not be supported: {extensions_required}")

            # Check for geometry
            meshes = gltf_data.get('meshes', [])
            if not meshes:
                issues.append("No meshes found in GLTF file")

            # Check for scenes
            scenes = gltf_data.get('scenes', [])
            if not scenes:
                issues.append("No scenes found in GLTF file")

            # Validate accessor references
            accessors = gltf_data.get('accessors', [])
            for mesh in meshes:
                for primitive in mesh.get('primitives', []):
                    attributes = primitive.get('attributes', {})
                    for attr_name, accessor_idx in attributes.items():
                        if accessor_idx >= len(accessors):
                            issues.append(f"Invalid accessor reference in mesh: {accessor_idx}")

        except json.JSONDecodeError as e:
            issues.append(f"Invalid JSON in GLTF file: {str(e)}")
        except Exception as e:
            issues.append(f"Validation error: {str(e)}")

        is_valid = len(issues) == 0
        return is_valid, issues

    def get_associated_files(self, file_path: Path) -> List[Path]:
        """Get binary buffer and texture files associated with GLTF."""
        associated = []

        try:
            # Only for .gltf files (GLB is self-contained)
            if file_path.suffix.lower() == '.gltf':
                gltf_data = self._parse_gltf_file(file_path)

                # Check for external buffers
                buffers = gltf_data.get('buffers', [])
                for buffer in buffers:
                    uri = buffer.get('uri')
                    if uri and not uri.startswith('data:'):  # Not a data URI
                        buffer_path = file_path.parent / uri
                        if buffer_path.exists():
                            associated.append(buffer_path)

                # Check for external images
                images = gltf_data.get('images', [])
                for image in images:
                    uri = image.get('uri')
                    if uri and not uri.startswith('data:'):  # Not a data URI
                        image_path = file_path.parent / uri
                        if image_path.exists():
                            associated.append(image_path)

        except Exception as e:
            self.logger.warning(f"Failed to find GLTF associated files: {e}")

        return associated

    def get_capabilities(self) -> Dict[str, bool]:
        """Get GLTF-specific capabilities."""
        capabilities = super().get_capabilities()
        capabilities.update({
            'conversion_target': True,   # Many tools can export to GLTF
            'conversion_source': True,   # Many tools can import GLTF
            'animation_support': True,   # GLTF supports animation
            'skeletal_support': True,    # GLTF supports skeletons
            'material_support': True,    # GLTF has PBR materials
        })
        return capabilities

    def extract_metadata_extras(self, file_path: Path) -> Dict[str, Any]:
        """Extract GLTF-specific metadata."""
        extras = {
            'is_binary_glb': file_path.suffix.lower() == '.glb',
            'file_size_bytes': file_path.stat().st_size
        }

        try:
            if file_path.suffix.lower() == '.glb':
                gltf_data = self._parse_glb_file(file_path)
            else:
                gltf_data = self._parse_gltf_file(file_path)

            # Extract asset metadata
            asset = gltf_data.get('asset', {})
            extras.update({
                'generator': asset.get('generator'),
                'copyright': asset.get('copyright'),
                'gltf_version': asset.get('version', '2.0')
            })

            # Count elements
            extras.update({
                'scene_count': len(gltf_data.get('scenes', [])),
                'node_count': len(gltf_data.get('nodes', [])),
                'mesh_count': len(gltf_data.get('meshes', [])),
                'animation_count': len(gltf_data.get('animations', [])),
                'skin_count': len(gltf_data.get('skins', []))
            })

        except Exception as e:
            extras['metadata_error'] = str(e)

        return extras