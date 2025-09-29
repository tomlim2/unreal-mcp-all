import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests

class RobloxAvatar3DDownloader:
    def __init__(self, download_folder: str = "real_3d_avatars", progress_callback=None):
		# 다운로드 폴더 준비
        self.download_folder = Path(download_folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)

        # Progress callback for integration with async jobs
        self.progress_callback = progress_callback

        # 세션 생성
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
            }
        )

    def get_user_info(self, user_id: int) -> Optional[Dict]:
        try:
            url = f"https://users.roblox.com/v1/users/{user_id}"
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"❌ 유저 정보 가져오기 실패 (ID: {user_id}): {e}")
            return None

    def get_user_id_by_username(self, username: str) -> Optional[int]:
        """유저명으로 유저 ID 찾기"""
        try:
            url = "https://users.roblox.com/v1/usernames/users"
            data = {"usernames": [username]}
            resp = self.session.post(url, json=data, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            if result.get("data"):
                user = result["data"][0]
                uid = user.get("id")
                uname = user.get("name")
                print(f"✅ 유저명 '{username}' → ID: {uid} (@{uname})")
                return uid
            print(f"❌ 유저명 '{username}'을 찾을 수 없습니다.")
            return None
        except requests.RequestException as e:
            print(f"❌ 유저 ID 검색 실패 ({username}): {e}")
            return None

    def resolve_user_input(self, user_input: str) -> Optional[int]:
        """입력을 유저 ID로 변환 (숫자면 ID, 아니면 유저명)"""
        s = user_input.strip()
        if s.isdigit():
            uid = int(s)
            print(f"🔍 유저 ID {uid}로 인식")
            return uid
        print(f"🔍 유저명 '{s}'으로 검색 중...")
        return self.get_user_id_by_username(s)

    def _fetch_thumbnail_generic(self, endpoint: str, user_id: int, size: str = "420x420") -> List[Dict]:
        try:
            url = f"https://thumbnails.roblox.com/v1/users/{endpoint}"
            params = {
                "userIds": str(user_id),
                "size": size,
                "format": "Png",
                "isCircular": "false",
            }
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            js = resp.json()
            return js.get("data", []) or []
        except Exception as e:
            print(f"⚠️ 썸네일 가져오기 실패 ({endpoint}): {e}")
            return []

    def get_avatar_thumbnails(self, user_id: int, sizes: List[str]) -> Dict[str, List[Dict]]:
        """요청한 여러 사이즈의 avatar/headshot/bust 썸네일 JSON 목록 수집"""
        result: Dict[str, List[Dict]] = {"avatar": [], "headshot": [], "bust": []}
        for size in sizes:
            result["avatar"].extend(self._fetch_thumbnail_generic("avatar", user_id, size))
            result["headshot"].extend(self._fetch_thumbnail_generic("avatar-headshot", user_id, size))
            result["bust"].extend(self._fetch_thumbnail_generic("avatar-bust", user_id, size))
            time.sleep(0.15)
        return result

    def download_thumbnails(self, user_id: int, user_folder: Path, sizes: List[str]) -> Dict[str, List[str]]:
        """썸네일 이미지 다운로드 후 로컬 파일 경로를 목록으로 반환

        Returns:
            Dict[str, List[str]]: {"avatar": [...], "headshot": [...], "bust": [...]} 파일 경로 리스트
        """
        thumb_meta = self.get_avatar_thumbnails(user_id, sizes)
        out: Dict[str, List[str]] = {"avatar": [], "headshot": [], "bust": []}
        tdir = user_folder / "thumbnails"
        tdir.mkdir(exist_ok=True)

        def _save(items: List[Dict], prefix: str, size: str, index: int) -> Optional[str]:
            image_url = items[index].get("imageUrl") if index < len(items) else None
            state = items[index].get("state") if index < len(items) else None
            if not image_url or state != "Completed":
                return None
            fname = f"{prefix}_{size}.png"
            fpath = tdir / fname
            try:
                r = self.session.get(image_url, timeout=30)
                if r.status_code == 200:
                    with open(fpath, "wb") as f:
                        f.write(r.content)
                    return str(fpath)
            except Exception:
                return None
            return None

        for size in sizes:
            # avatar
            size_avatar = [d for d in thumb_meta["avatar"] if d.get("requestedUrl", "").find(f"size={size}") != -1 or size in d.get("imageUrl", "")]
            if size_avatar:
                p = _save(size_avatar, "avatar", size, 0)
                if p: out["avatar"].append(p)
            # headshot
            size_head = [d for d in thumb_meta["headshot"] if d.get("requestedUrl", "").find(f"size={size}") != -1 or size in d.get("imageUrl", "")]
            if size_head:
                p = _save(size_head, "headshot", size, 0)
                if p: out["headshot"].append(p)
            # bust
            size_bust = [d for d in thumb_meta["bust"] if d.get("requestedUrl", "").find(f"size={size}") != -1 or size in d.get("imageUrl", "")]
            if size_bust:
                p = _save(size_bust, "bust", size, 0)
                if p: out["bust"].append(p)
        return out

    # ----------------------
    # 3D 메타데이터 & CDN
    # ----------------------
    def calculate_cdn_url(self, hash_id: str) -> str:
        """해시 ID에서 CDN URL 계산 (2024 알고리즘 추정치)"""
        i = 31
        for t in range(min(38, len(hash_id))):
            i ^= ord(hash_id[t])
        cdn_number = i % 8
        return f"https://t{cdn_number}.rbxcdn.com/{hash_id}"

    def get_avatar_3d_metadata(self, user_id: int, max_attempts: int = 10, delay: float = 1.0) -> Optional[Dict]:
        """3D 아바타 메타데이터 가져오기 (폴링 및 백오프 포함)"""
        try:
            url = "https://thumbnails.roblox.com/v1/users/avatar-3d"
            params = {"userId": user_id}

            for attempt in range(1, max_attempts + 1):
                r1 = self.session.get(url, params=params, timeout=30)

                if r1.status_code == 429:
                    backoff = min(5.0, delay * attempt)
                    print(f"⏳ API 제한(429). {backoff:.1f}s 대기 후 재시도 {attempt}/{max_attempts}")
                    time.sleep(backoff)
                    continue

                r1.raise_for_status()
                data = r1.json()
                state = data.get("state")

                if state == "Completed":
                    image_url = data.get("imageUrl")
                    if not image_url:
                        print("❌ imageUrl 없음")
                        return None

                    r2 = self.session.get(image_url, timeout=30)
                    r2.raise_for_status()
                    try:
                        meta = r2.json()
                    except json.JSONDecodeError:
                        print("❌ JSON 파싱 실패 (imageUrl 응답)")
                        return None

                    print("✅ 3D 메타데이터 획득 완료")
                    return meta

                # 아직 준비 안됨 → 대기 후 재시도
                if state in ("Pending", "InProgress", "InProgress_Unknown", None):
                    if attempt < max_attempts:
                        time.sleep(delay)
                        continue
                    print(f"⚠️ 아바타 처리 상태가 완료되지 않음: {state}")
                    return None

                # 알 수 없는 상태
                print(f"⚠️ 예기치 않은 상태: {state}")
                return None

        except requests.RequestException as e:
            print(f"❌ 3D 메타데이터 가져오기 실패: {e}")
            return None
        except Exception as e:
            print(f"❌ 3D 메타데이터 처리 중 예외: {e}")
            return None

    def download_file_from_hash(self, hash_id: str, file_path: Path, file_type: str = "파일") -> bool:
        """해시 ID로 파일 다운로드 (다중 CDN 시도)"""
        headers = {
            "User-Agent": self.session.headers["User-Agent"],
            "Referer": "https://www.roblox.com/",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }

        # 시도할 URL 목록
        candidates: List[str] = []
        try:
            candidates.append(self.calculate_cdn_url(hash_id))
        except Exception as e:
            print(f"⚠️ 기본 CDN URL 계산 실패: {e}")

        for n in range(8):
            u = f"https://t{n}.rbxcdn.com/{hash_id}"
            if u not in candidates:
                candidates.append(u)
        extra = [
            f"https://tr.rbxcdn.com/{hash_id}",
            f"https://c0.rbxcdn.com/{hash_id}",
            f"https://c1.rbxcdn.com/{hash_id}",
        ]
        for u in extra:
            if u not in candidates:
                candidates.append(u)

        print(f"➡️ {file_type} 다운로드 시도...")

        # Notify progress callback if available
        if self.progress_callback:
            try:
                self.progress_callback("downloading", file_type)
            except:
                pass  # Don't fail download if callback fails

        for i, url in enumerate(candidates):
            try:
                label = "기본 서버" if i == 0 else f"대체 서버 #{i}"
                print(f"   🔄 {label}: {url}")
                resp = self.session.get(url, headers=headers, stream=True, timeout=30, allow_redirects=True)
                if resp.status_code == 200:
                    with open(file_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    if file_path.exists() and file_path.stat().st_size > 0:
                        print(f"   ✅ {file_type} 다운로드 완료: {file_path}")

                        # Notify progress callback of successful download
                        if self.progress_callback:
                            try:
                                self.progress_callback("completed", file_type)
                            except:
                                pass

                        return True
                    else:
                        print("   ⚠️ 빈 파일, 다음 서버 시도")
                        if file_path.exists():
                            file_path.unlink()
                else:
                    print(f"   ❌ HTTP {resp.status_code}: {resp.reason}")
            except requests.Timeout:
                print("   ⏰ 타임아웃, 다음 서버 시도")
            except requests.ConnectionError:
                print("   🔌 연결 오류, 다음 서버 시도")
            except requests.RequestException as e:
                print(f"   ❌ 요청 오류: {e}")
            except Exception as e:
                print(f"   ❌ 예외: {e}")

            if i < len(candidates) - 1:
                time.sleep(0.4)

        print(f"   💔 모든 CDN 서버에서 {file_type} 다운로드 실패")

        # Notify progress callback of failed download
        if self.progress_callback:
            try:
                self.progress_callback("failed", file_type)
            except:
                pass

        return False

    # ----------------------
    # 메인 다운로드 플로우
    # ----------------------
    def download_avatar_3d_complete(self, user_id: int, include_textures: bool = True, include_thumbnails: bool = False, thumbnail_sizes: Optional[List[str]] = None) -> bool:
        """완전한 3D 아바타 다운로드 (OBJ + MTL + 텍스처 + 선택적 2D 썸네일)

        Args:
            user_id: 대상 유저 ID
            include_textures: 3D 텍스처(hash 기반) 다운로드 여부
            include_thumbnails: 2D avatar/headshot/bust 썸네일도 함께 다운로드할지 여부
            thumbnail_sizes: 저장할 썸네일 사이즈 목록 (기본: ["150x150", "420x420"]) 
        """
        print(f"🎯 유저 ID {user_id}의 완전한 3D 아바타 다운로드 시작...")

        # Notify progress callback of start
        if self.progress_callback:
            try:
                self.progress_callback("started", f"user_{user_id}")
            except:
                pass

        user_info = self.get_user_info(user_id)
        if not user_info:
            return False

        username = user_info.get("name", f"user_{user_id}")
        display_name = user_info.get("displayName", username)
        print(f"👤 {display_name} (@{username})")

        # Notify progress callback of user resolution
        if self.progress_callback:
            try:
                self.progress_callback("user_resolved", username)
            except:
                pass

        metadata = self.get_avatar_3d_metadata(user_id)
        if not metadata:
            return False

        # Notify progress callback of metadata fetch
        if self.progress_callback:
            try:
                self.progress_callback("metadata_fetched", f"{username}_metadata")
            except:
                pass

        # 폴더 준비
        user_folder = self.download_folder / f"{username}_{user_id}_3D"
        user_folder.mkdir(exist_ok=True)
        textures_folder = user_folder / "textures"
        if include_textures:
            textures_folder.mkdir(exist_ok=True)
        thumbnail_folder = user_folder / "thumbnails"
        if include_thumbnails:
            thumbnail_folder.mkdir(exist_ok=True)

        total_files = 0
        success_count = 0

        # OBJ
        obj_hash = metadata.get("obj")
        if obj_hash:
            total_files += 1
            if self.download_file_from_hash(obj_hash, user_folder / "avatar.obj", "OBJ 모델"):
                success_count += 1

        # MTL
        mtl_hash = metadata.get("mtl")
        if mtl_hash:
            total_files += 1
            if self.download_file_from_hash(mtl_hash, user_folder / "avatar.mtl", "MTL 재질"):
                success_count += 1

        # 텍스처
        textures = []
        if include_textures:
            textures = metadata.get("textures", []) or []
            if textures:
                print(f"🎨 {len(textures)}개의 텍스처 다운로드 중...")
            texture_success = 0
            for i, th in enumerate(textures):
                total_files += 1
                tf = textures_folder / f"texture_{i+1:03d}.png"
                if self.download_file_from_hash(th, tf, f"텍스처 {i+1}"):
                    success_count += 1
                    texture_success += 1
                if i < len(textures) - 1:
                    time.sleep(0.25)
            if textures:
                print(f"   🎨 텍스처 다운로드 결과: {texture_success}/{len(textures)} 성공")

        # 확장 정보/분석 및 저장물 생성
        extended_info = self.get_extended_avatar_info(user_id)
        thumbnail_files: Optional[Dict[str, List[str]]] = None
        if include_thumbnails:
            if not thumbnail_sizes:
                thumbnail_sizes = ["150x150", "420x420"]
            print(f"🖼️ 썸네일 다운로드: {thumbnail_sizes}")
            thumbnail_files = self.download_thumbnails(user_id, user_folder, thumbnail_sizes)
            # extended_info에 썸네일 로컬 경로 기록(요약)
            if extended_info is not None:
                extended_info["downloaded_thumbnails"] = thumbnail_files
        if (user_folder / "avatar.obj").exists():
            try:
                extended_info["obj_structure"] = self.analyze_obj_structure(user_folder / "avatar.obj")
            except Exception as e:
                extended_info["obj_structure_error"] = str(e)
        # 메타데이터 저장 (함수 내부 들여쓰기 복구)
        self.save_metadata(user_info, metadata, user_folder, extended_info)

        # 성공 판정 (OBJ 또는 MTL 중 하나라도 성공)
        core_ok = int((user_folder / "avatar.obj").exists()) + int((user_folder / "avatar.mtl").exists())
        print(f"\n🎉 다운로드 완료: {success_count}/{total_files} 파일 성공")
        if core_ok > 0:
            print(f"📁 저장 위치: {user_folder}")
            print("📦 포함된 파일:")
            if (user_folder / "avatar.obj").exists():
                print("   📄 avatar.obj (3D 모델)")
            if (user_folder / "avatar.mtl").exists():
                print("   🎨 avatar.mtl (재질 정보)")
            if include_textures and textures:
                got = len(list(textures_folder.glob("texture_*.png")))
                print(f"   🖼️ textures/ ({got}/{len(textures)}개 텍스처)")
            if include_thumbnails and thumbnail_files:
                avc = len(thumbnail_files.get("avatar", [])) if thumbnail_files else 0
                hdc = len(thumbnail_files.get("headshot", [])) if thumbnail_files else 0
                bsc = len(thumbnail_files.get("bust", [])) if thumbnail_files else 0
                print(f"   🖼️ thumbnails/ (avatar:{avc} headshot:{hdc} bust:{bsc})")
            print("   📋 metadata.json (상세 정보)")
            print("   📖 README.md (사용법)")
            return True
        else:
            print("   ❌ 핵심 3D 파일 다운로드 실패")
            return False

    # ----------------------
    # 확장 정보/분석/문서화
    # ----------------------
    def get_extended_avatar_info(self, user_id: int) -> Dict:
        """여러 부가 API에서 정보 수집 (실패 무시)"""
        info: Dict = {
            "user_id": user_id,
            "collected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "api_responses": {},
        }

        def safe_get(name: str, url: str):
            try:
                r = self.session.get(url, timeout=30)
                if r.status_code == 200:
                    info["api_responses"][name] = r.json()
            except Exception:
                pass

        safe_get("avatar_config", f"https://avatar.roblox.com/v1/users/{user_id}/avatar")
        safe_get("currently_wearing", f"https://avatar.roblox.com/v1/users/{user_id}/currently-wearing")
        safe_get(
            "thumbnails",
            f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=720x720&format=Png&isCircular=false",
        )
        safe_get("games", f"https://games.roblox.com/v2/users/{user_id}/games?accessFilter=Public&limit=10")
        safe_get("groups", f"https://groups.roblox.com/v2/users/{user_id}/groups/roles")
        return info

    def _infer_rig_from_obj(self, obj_structure: Dict) -> str:
        """OBJ 그룹/이름 패턴으로 대략적인 리깅 타입 추정 (최후의 보루)"""
        try:
            groups = [g.get("name", "").lower() for g in obj_structure.get("groups", [])]
            # R15는 Upper/Lower/Hand/Foot 등 세분화가 흔함
            r15_markers = ("upper", "lower", "hand", "foot", "upperarm", "lowerarm", "upperleg", "lowerleg")
            if any(m in name for name in groups for m in r15_markers):
                return "R15"
            # 그룹 수가 적으면 R6 가능성이 높음 (아주 러프한 휴리스틱)
            if len(groups) <= 8:
                return "R6"
        except Exception:
            pass
        return "Unknown"

    def _extract_avatar_type(self, extended_info: Optional[Dict], obj_structure: Optional[Dict]) -> str:
        """확장 정보(avatar_config) → OBJ 휴리스틱 순으로 R6/R15 추정"""
        # 1) avatar_config의 playerAvatarType 사용 (가장 신뢰도 높음)
        try:
            if extended_info and extended_info.get("api_responses", {}).get("avatar_config"):
                avatar_config = extended_info["api_responses"]["avatar_config"]
                at = avatar_config.get("playerAvatarType")
                if isinstance(at, str) and at.strip():
                    return at
        except Exception:
            pass
        # 2) OBJ 구조 기반 휴리스틱
        if obj_structure:
            return self._infer_rig_from_obj(obj_structure)
        return "Unknown"

    def analyze_obj_structure(self, obj_path: Path) -> Dict:
        """OBJ 파일 구조 간단 분석"""
        result: Dict = {
            "file_path": str(obj_path),
            "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "groups": [],
            "materials": [],
            "vertices": 0,
            "faces": 0,
            "normals": 0,
            "texture_coords": 0,
            "body_parts": [],
        }
        with open(obj_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, raw in enumerate(f, 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("v "):
                    result["vertices"] += 1
                elif line.startswith("vn "):
                    result["normals"] += 1
                elif line.startswith("vt "):
                    result["texture_coords"] += 1
                elif line.startswith("f "):
                    result["faces"] += 1
                elif line.startswith("g "):
                    name = line[2:].strip()
                    g = {"name": name, "line": line_num, "type": self.classify_body_part(name)}
                    result["groups"].append(g)
                    if g["type"] != "unknown":
                        result["body_parts"].append(g)
                elif line.startswith("usemtl "):
                    mtl = line[7:].strip()
                    if mtl and mtl not in result["materials"]:
                        result["materials"].append(mtl)
        return result

    def classify_body_part(self, group_name: str) -> str:
        """그룹 이름으로 바디 파트 추정 분류"""
        n = group_name.lower()
        mapping = {
            "head": ["player1", "head"],
            "torso": ["player2", "torso", "chest"],
            "left_arm": ["player3", "leftarm", "left_arm"],
            "right_arm": ["player4", "rightarm", "right_arm"],
            "left_leg": ["player5", "leftleg", "left_leg"],
            "right_leg": ["player6", "rightleg", "right_leg"],
            "hat": ["player7", "hat", "cap", "helmet"],
            "hair": ["player8", "hair"],
            "face": ["player9", "face"],
            "shirt": ["player10", "shirt", "top"],
            "pants": ["player11", "pants", "bottom"],
            "shoes": ["player12", "shoes", "boot"],
            "accessory": ["player13", "player14", "player15", "accessory", "gear"],
            "handle": ["handle", "grip", "tool"],
        }
        for part, keys in mapping.items():
            if any(k in n for k in keys):
                return part
        return "unknown"

    def save_metadata(
        self,
        user_info: Dict,
        metadata: Dict,
        user_folder: Path,
        extended_info: Optional[Dict] = None,
    ) -> None:
        """메타데이터와 README 저장"""
        # 가능한 경우 OBJ 구조를 먼저 확보 (extended_info에서)
        obj_structure = None
        if extended_info and isinstance(extended_info, dict):
            obj_structure = extended_info.get("obj_structure")

        avatar_type = self._extract_avatar_type(extended_info, obj_structure)

        full = {
            "user_info": user_info,
            "avatar_3d_metadata": metadata,
            "download_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "avatar_type": avatar_type,
            "api_info": {
                "source": "Roblox Avatar 3D API",
                "endpoint": "https://thumbnails.roblox.com/v1/users/avatar-3d",
                "cdn_calculation": "Updated 2024 hash algorithm (heuristic)",
            },
        }
        if extended_info is not None:
            full["extended_avatar_info"] = extended_info

        with open(user_folder / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(full, f, indent=2, ensure_ascii=False)

        self.create_extended_readme(user_info, metadata, user_folder, extended_info)

    def create_extended_readme(
        self,
        user_info: Dict,
        metadata: Dict,
        user_folder: Path,
        extended_info: Optional[Dict] = None,
    ) -> None:
        """README 생성 (간결 버전)"""
        camera = metadata.get("camera", {})
        aabb = metadata.get("aabb", {})

        # 아바타 타입 결정 (README 표기)
        obj_structure = None
        if extended_info and isinstance(extended_info, dict):
            obj_structure = extended_info.get("obj_structure")
        avatar_type = self._extract_avatar_type(extended_info, obj_structure)

        lines: List[str] = []
        lines.append("# 3D 아바타 모델 사용법")
        lines.append("")
        lines.append("## 📁 다운로드된 파일들")
        lines.append("- avatar.obj: 3D 메시 파일 (OBJ)")
        lines.append("- avatar.mtl: 재질 정보 파일 (MTL)")
        lines.append("- textures/: 텍스처 이미지들")
        lines.append("- metadata.json: 전체 메타데이터")
        lines.append("- thumbnails/: (선택) 2D 아바타/헤드샷/흉상 이미지")
        lines.append("")
        lines.append("## 🎮 유저 정보")
        lines.append(f"- 이름: {user_info.get('displayName')} (@{user_info.get('name')})")
        lines.append(f"- 유저 ID: {user_info.get('id')}")
        lines.append(f"- 가입일: {user_info.get('created', 'N/A')}")
        lines.append(f"- 다운로드 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- 아바타 타입: {avatar_type}")
        lines.append("")
        lines.append("## 📐 3D 모델 정보")
        lines.append(f"- 카메라 위치: {camera.get('position', 'N/A')}")
        lines.append(f"- 카메라 FOV: {camera.get('fov', 'N/A')}")
        lines.append(f"- 바운딩 박스: {aabb.get('min', 'N/A')} ~ {aabb.get('max', 'N/A')}")
        lines.append("")
        lines.append("## 🛠️ 사용 방법")
        lines.append("")
        lines.append("### Blender에서 사용하기")
        lines.append("1. File > Import > Wavefront (.obj)")
        lines.append("2. avatar.obj 선택 후 임포트 (mtl 자동 적용)")
        lines.append("")
        lines.append("### Unity에서 사용하기")
        lines.append("1. 프로젝트 Assets 폴더에 모든 파일 복사")
        lines.append("2. avatar.obj를 씬에 드래그")
        lines.append("3. 필요 시 텍스처를 재질에 수동 연결")
        lines.append("")
        lines.append("### Three.js 예시")
        lines.append("```javascript")
        lines.append("import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js';")
        lines.append("import { MTLLoader } from 'three/examples/jsm/loaders/MTLLoader.js';")
        lines.append("")
        lines.append("const mtlLoader = new MTLLoader();")
        lines.append("mtlLoader.load('avatar.mtl', (materials) => {")
        lines.append("  materials.preload();")
        lines.append("  const objLoader = new OBJLoader();")
        lines.append("  objLoader.setMaterials(materials);")
        lines.append("  objLoader.load('avatar.obj', (object) => {")
        lines.append("    scene.add(object);")
        lines.append("  });")
        lines.append("});")
        lines.append("```")
        lines.append("")
        lines.append("## ⚠️ 주의사항")
        lines.append("- 이 모델은 로블록스 R15/R6 형식입니다")
        lines.append("- 상업적 사용 시 로블록스 이용약관을 준수하세요")
        lines.append("")
        lines.append("## 🔧 문제 해결")
        lines.append("- 텍스처가 보이지 않으면 MTL 경로를 확인하세요")
        lines.append("- 모델이 투명하면 재질의 투명도/알파 설정을 점검하세요")
        lines.append("")
        readme = "\n".join(lines) + "\n"
        with open(user_folder / "README.md", "w", encoding="utf-8") as f:
            f.write(readme)
        print(f"📋 사용법 안내 파일 생성: {user_folder / 'README.md'}")



def main() -> None:
    print("=== 로블록스 3D 아바타 다운로더 (최신 API) ===\n")
    downloader = RobloxAvatar3DDownloader("real_3d_avatars")

    try:
        user_input = input("유저 ID 또는 유저명 입력: ").strip()
        user_id = downloader.resolve_user_input(user_input)
        if user_id is None:
            print("❌ 유효한 유저를 찾을 수 없습니다.")
            return

        downloader.download_avatar_3d_complete(user_id, True, True, None)

    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")


if __name__ == "__main__":
    main()
