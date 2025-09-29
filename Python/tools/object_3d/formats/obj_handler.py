"""
OBJ Format Handler for Wavefront OBJ files.

Handles analysis, validation, and processing of OBJ/MTL files.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
from .base import BaseFormatHandler


class OBJFormatHandler(BaseFormatHandler):
    """Handler for Wavefront OBJ format files."""

    def __init__(self):
        super().__init__("Wavefront OBJ", ['.obj', '.mtl'])

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze OBJ file structure and extract metadata."""
        analysis = {
            'vertex_count': 0,
            'face_count': 0,
            'triangle_count': 0,
            'normal_count': 0,
            'texture_coord_count': 0,
            'bounding_box': {"min": [float('inf')] * 3, "max": [float('-inf')] * 3},
            'has_normals': False,
            'has_texture_coords': False,
            'material_references': [],
            'groups': [],
            'format_specific': {
                'smoothing_groups': [],
                'parameter_vertices': 0,
                'curves': 0,
                'surfaces': 0
            }
        }

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                current_smoothing_group = None

                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split()
                    if not parts:
                        continue

                    command = parts[0]

                    try:
                        if command == 'v' and len(parts) >= 4:
                            # Vertex coordinate
                            analysis['vertex_count'] += 1
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            # Update bounding box
                            for i, coord in enumerate([x, y, z]):
                                analysis['bounding_box']['min'][i] = min(analysis['bounding_box']['min'][i], coord)
                                analysis['bounding_box']['max'][i] = max(analysis['bounding_box']['max'][i], coord)

                        elif command == 'vn':
                            # Vertex normal
                            analysis['normal_count'] += 1
                            analysis['has_normals'] = True

                        elif command == 'vt':
                            # Texture coordinate
                            analysis['texture_coord_count'] += 1
                            analysis['has_texture_coords'] = True

                        elif command == 'vp':
                            # Parameter space vertex
                            analysis['format_specific']['parameter_vertices'] += 1

                        elif command == 'f':
                            # Face
                            analysis['face_count'] += 1
                            # Estimate triangle count (face with n vertices = n-2 triangles)
                            vertex_count_in_face = len(parts) - 1
                            if vertex_count_in_face >= 3:
                                analysis['triangle_count'] += max(1, vertex_count_in_face - 2)

                        elif command == 'usemtl' and len(parts) >= 2:
                            # Material reference
                            material = parts[1]
                            if material not in analysis['material_references']:
                                analysis['material_references'].append(material)

                        elif command == 'g' and len(parts) >= 2:
                            # Group
                            group_name = ' '.join(parts[1:])
                            analysis['groups'].append(group_name)

                        elif command == 'o' and len(parts) >= 2:
                            # Object name (similar to group)
                            object_name = ' '.join(parts[1:])
                            analysis['groups'].append(f"object:{object_name}")

                        elif command == 's':
                            # Smoothing group
                            if len(parts) >= 2:
                                smoothing_group = parts[1]
                                if smoothing_group != 'off' and smoothing_group not in analysis['format_specific']['smoothing_groups']:
                                    analysis['format_specific']['smoothing_groups'].append(smoothing_group)

                        elif command in ['curv', 'curv2']:
                            # Curve
                            analysis['format_specific']['curves'] += 1

                        elif command in ['surf']:
                            # Surface
                            analysis['format_specific']['surfaces'] += 1

                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"Error parsing line {line_num} in {file_path}: {e}")
                        continue

            # Handle infinite bounding box (no vertices found)
            if analysis['vertex_count'] == 0:
                analysis['bounding_box'] = {"min": [0.0, 0.0, 0.0], "max": [0.0, 0.0, 0.0]}

        except Exception as e:
            self.logger.error(f"Error analyzing OBJ file {file_path}: {e}")
            analysis['analysis_error'] = str(e)

        return analysis

    def validate_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate OBJ file for common issues."""
        issues = []

        try:
            # Basic file existence and readability
            if not file_path.exists():
                return False, ["File does not exist"]

            if file_path.stat().st_size == 0:
                return False, ["File is empty"]

            # Analyze structure
            analysis = self.analyze_file(file_path)

            # Check for analysis errors
            if 'analysis_error' in analysis:
                issues.append(f"Analysis error: {analysis['analysis_error']}")

            # Geometry validation
            vertex_count = analysis.get('vertex_count', 0)
            face_count = analysis.get('face_count', 0)

            if vertex_count == 0:
                issues.append("No vertices found in OBJ file")

            if face_count == 0:
                issues.append("No faces found in OBJ file")

            # Check for extremely low-quality models
            if vertex_count > 0 and vertex_count < 3:
                issues.append(f"Very low vertex count ({vertex_count}) for a 3D model")

            if face_count > 0 and face_count < 1:
                issues.append(f"Very low face count ({face_count}) for a 3D model")

            # Material validation
            material_refs = analysis.get('material_references', [])
            if material_refs:
                # Check for MTL file
                mtl_file = file_path.with_suffix('.mtl')
                if not mtl_file.exists():
                    issues.append(f"OBJ references materials but MTL file not found: {mtl_file}")

            # Check bounding box validity
            bbox = analysis.get('bounding_box', {})
            min_coords = bbox.get('min', [0, 0, 0])
            max_coords = bbox.get('max', [0, 0, 0])

            if any(coord == float('inf') or coord == float('-inf') for coord in min_coords + max_coords):
                issues.append("Invalid bounding box coordinates")

            # Warn about advanced features that may not be widely supported
            format_specific = analysis.get('format_specific', {})
            if format_specific.get('curves', 0) > 0:
                issues.append("File contains curves which may not be supported by all software")

            if format_specific.get('surfaces', 0) > 0:
                issues.append("File contains NURBS surfaces which may not be supported by all software")

        except Exception as e:
            issues.append(f"Validation error: {str(e)}")

        is_valid = len(issues) == 0
        return is_valid, issues

    def get_associated_files(self, file_path: Path) -> List[Path]:
        """Get MTL and texture files associated with OBJ."""
        associated = []

        # Check for MTL file
        mtl_file = file_path.with_suffix('.mtl')
        if mtl_file.exists():
            associated.append(mtl_file)

            # Parse MTL to find texture references
            try:
                texture_files = self._extract_texture_references(mtl_file)
                for texture_file in texture_files:
                    texture_path = file_path.parent / texture_file
                    if texture_path.exists():
                        associated.append(texture_path)

            except Exception as e:
                self.logger.warning(f"Failed to extract texture references from {mtl_file}: {e}")

        return associated

    def _extract_texture_references(self, mtl_file: Path) -> List[str]:
        """Extract texture file references from MTL file."""
        texture_files = []

        texture_keywords = [
            'map_Kd',  # Diffuse map
            'map_Ks',  # Specular map
            'map_Ka',  # Ambient map
            'map_Ke',  # Emissive map
            'map_Ns',  # Shininess map
            'map_d',   # Alpha map
            'map_bump', 'bump',  # Bump maps
            'disp',    # Displacement map
            'refl',    # Reflection map
        ]

        try:
            with open(mtl_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split()
                    if len(parts) >= 2 and parts[0] in texture_keywords:
                        texture_filename = parts[-1]  # Last part is usually the filename
                        if texture_filename not in texture_files:
                            texture_files.append(texture_filename)

        except Exception as e:
            self.logger.warning(f"Error reading MTL file {mtl_file}: {e}")

        return texture_files

    def get_capabilities(self) -> Dict[str, bool]:
        """Get OBJ-specific capabilities."""
        capabilities = super().get_capabilities()
        capabilities.update({
            'conversion_target': True,   # Many tools can export to OBJ
            'conversion_source': True,   # Many tools can import OBJ
            'animation_support': False,  # OBJ doesn't support animation
            'skeletal_support': False,   # OBJ doesn't support skeletons
            'material_support': True,    # MTL materials
        })
        return capabilities

    def extract_metadata_extras(self, file_path: Path) -> Dict[str, Any]:
        """Extract OBJ-specific metadata."""
        extras = {}

        try:
            # Check for MTL file and extract material info
            mtl_file = file_path.with_suffix('.mtl')
            if mtl_file.exists():
                extras['has_mtl_file'] = True
                extras['mtl_materials'] = self._extract_material_names(mtl_file)
                extras['texture_references'] = self._extract_texture_references(mtl_file)
            else:
                extras['has_mtl_file'] = False

            # Add file size info
            extras['file_size_bytes'] = file_path.stat().st_size

        except Exception as e:
            self.logger.warning(f"Failed to extract OBJ metadata extras: {e}")
            extras['metadata_error'] = str(e)

        return extras

    def _extract_material_names(self, mtl_file: Path) -> List[str]:
        """Extract material names from MTL file."""
        materials = []

        try:
            with open(mtl_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('newmtl ') and len(line.split()) >= 2:
                        material_name = ' '.join(line.split()[1:])
                        materials.append(material_name)

        except Exception as e:
            self.logger.warning(f"Error extracting material names from {mtl_file}: {e}")

        return materials