"""
Session context data structures for persistent chat conversations.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional
import json


@dataclass
class ChatMessage:
    """Represents a single message in the conversation."""
    timestamp: datetime
    role: str  # 'user', 'assistant', 'system'
    content: str
    commands: List[Dict[str, Any]] = field(default_factory=list)
    execution_results: List[Dict[str, Any]] = field(default_factory=list)
    # NEW: Job-related fields for worker pattern
    job_id: Optional[str] = None
    job_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            'timestamp': self.timestamp.isoformat(),
            'role': self.role,
            'content': self.content,
            'commands': self.commands,
            'execution_results': self.execution_results
        }
        
        # Include job fields if present
        if self.job_id:
            data['job_id'] = self.job_id
        if self.job_info:
            data['job_info'] = self.job_info
            # Flatten important job fields for frontend compatibility
            if self.job_info.get('job_status'):
                data['job_status'] = self.job_info['job_status']
            if self.job_info.get('job_progress') is not None:
                data['job_progress'] = self.job_info['job_progress']
            if self.job_info.get('image_url'):
                data['image_url'] = self.job_info['image_url']
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            role=data['role'],
            content=data['content'],
            commands=data.get('commands', []),
            execution_results=data.get('execution_results', []),
            job_id=data.get('job_id'),
            job_info=data.get('job_info')
        )


@dataclass
class ActorInfo:
    """Information about an Unreal Engine actor."""
    name: str
    actor_class: str
    location: Optional[Dict[str, float]] = None
    rotation: Optional[Dict[str, float]] = None
    scale: Optional[Dict[str, float]] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LightInfo:
    """Information about a light actor."""
    name: str
    light_type: str  # 'PointLight', 'DirectionalLight', etc.
    intensity: float
    color: Dict[str, int]  # RGB values
    location: Optional[Dict[str, float]] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SceneState:
    """Current state of the Unreal Engine scene."""
    actors: List[ActorInfo] = field(default_factory=list)
    lights: List[LightInfo] = field(default_factory=list)
    sky_settings: Dict[str, Any] = field(default_factory=dict)
    cesium_location: Optional[Dict[str, float]] = None
    last_commands: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_from_command_result(self, command: str, params: Dict[str, Any], result: Dict[str, Any]):
        """Update scene state based on command execution result."""
        self.last_updated = datetime.now()
        
        # Track the command
        self.last_commands.append({
            'command': command,
            'params': params,
            'result': result,
            'timestamp': self.last_updated.isoformat()
        })
        
        # Keep only last 10 commands
        if len(self.last_commands) > 10:
            self.last_commands = self.last_commands[-10:]
        
        # Update specific scene elements based on command type
        if command == 'create_mm_control_light' and result.get('success'):
            light_info = LightInfo(
                name=result.get('actor_name', params.get('light_name', 'Unknown')),
                light_type='PointLight',
                intensity=result.get('intensity', params.get('intensity', 1000)),
                color=result.get('color', params.get('color', {'r': 255, 'g': 255, 'b': 255})),
                location=result.get('location', params.get('location'))
            )
            # Remove existing light with same name, add new one
            self.lights = [l for l in self.lights if l.name != light_info.name]
            self.lights.append(light_info)
            
        elif command == 'delete_mm_control_light' and result.get('success'):
            light_name = params.get('light_name')
            self.lights = [l for l in self.lights if l.name != light_name]
            
        elif command == 'set_cesium_latitude_longitude' and result.get('success'):
            self.cesium_location = {
                'latitude': result.get('latitude', params.get('latitude')),
                'longitude': result.get('longitude', params.get('longitude'))
            }
            
        elif command.startswith('set_') and 'sky' in command.lower() and result.get('success'):
            # Update sky settings
            if 'time_of_day' in params:
                self.sky_settings['time_of_day'] = params['time_of_day']
            if 'color_temperature' in params:
                self.sky_settings['color_temperature'] = params['color_temperature']
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'actors': [asdict(actor) for actor in self.actors],
            'lights': [asdict(light) for light in self.lights],
            'sky_settings': self.sky_settings,
            'cesium_location': self.cesium_location,
            'last_commands': self.last_commands,
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneState':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            actors=[ActorInfo(**actor) for actor in data.get('actors', [])],
            lights=[LightInfo(**light) for light in data.get('lights', [])],
            sky_settings=data.get('sky_settings', {}),
            cesium_location=data.get('cesium_location'),
            last_commands=data.get('last_commands', []),
            last_updated=datetime.fromisoformat(data.get('last_updated', datetime.now().isoformat()))
        )


@dataclass 
class SessionContext:
    """Complete session context including conversation and scene state."""
    session_id: str
    created_at: datetime
    last_accessed: datetime
    conversation_history: List[ChatMessage] = field(default_factory=list)
    scene_state: SceneState = field(default_factory=SceneState)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_name: Optional[str] = None
    llm_model: str = 'gemini-2'  # Default to Gemini 2.5 Flash model
    
    def add_message(self, role: str, content: str, commands: List[Dict[str, Any]] = None, 
                   execution_results: List[Dict[str, Any]] = None):
        """Add a new message to the conversation history."""
        message = ChatMessage(
            timestamp=datetime.now(),
            role=role,
            content=content,
            commands=commands or [],
            execution_results=execution_results or []
        )
        self.conversation_history.append(message)
        self.last_accessed = datetime.now()
        
        # Keep conversation history manageable (last 50 messages)
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def add_interaction(self, user_input: str, ai_response: Dict[str, Any]):
        """Add a complete user-AI interaction to the history."""
        # Add user message
        self.add_message('user', user_input)
        
        # Add AI response
        ai_content = ai_response.get('explanation', 'Processed your request')
        commands = ai_response.get('commands', [])
        execution_results = ai_response.get('executionResults', [])
        
        self.add_message('assistant', ai_content, commands, execution_results)
        
        # Update scene state based on executed commands
        for i, command in enumerate(commands):
            if i < len(execution_results):
                result = execution_results[i]
                if result.get('success'):
                    self.scene_state.update_from_command_result(
                        command.get('type', ''),
                        command.get('params', {}),
                        result.get('result', {})
                    )
    
    def add_job_message(self, job_id: str, job_status: str, content: str, 
                       job_progress: Optional[int] = None, image_url: Optional[str] = None):
        """Add a job status message to the conversation history."""
        job_info = {
            'job_status': job_status,
            'job_progress': job_progress,
            'image_url': image_url
        }
        
        message = ChatMessage(
            timestamp=datetime.now(),
            role='job',
            content=content,
            job_id=job_id,
            job_info=job_info
        )
        
        self.conversation_history.append(message)
        self.last_accessed = datetime.now()
        
        # Keep conversation history manageable (last 50 messages)
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def update_job_message(self, job_id: str, job_status: str, content: str = None,
                          job_progress: Optional[int] = None, image_url: Optional[str] = None):
        """Update an existing job message or create new one if not found."""
        # Find existing job message
        for message in reversed(self.conversation_history):
            if message.role == 'job' and message.job_id == job_id:
                # Update existing message
                message.job_info = message.job_info or {}
                message.job_info['job_status'] = job_status
                if job_progress is not None:
                    message.job_info['job_progress'] = job_progress
                if image_url:
                    message.job_info['image_url'] = image_url
                if content:
                    message.content = content
                message.timestamp = datetime.now()
                self.last_accessed = datetime.now()
                return
        
        # If not found, create new job message
        self.add_job_message(job_id, job_status, content or f"Job {job_id} status: {job_status}", 
                           job_progress, image_url)
    
    def get_conversation_summary(self, max_messages: int = 10) -> str:
        """Get a summary of recent conversation for AI context."""
        if not self.conversation_history:
            return "No previous conversation history."
        
        recent_messages = self.conversation_history[-max_messages:]
        summary_parts = []
        
        for msg in recent_messages:
            if msg.role == 'user':
                summary_parts.append(f"User: {msg.content}")
            elif msg.role == 'assistant':
                if msg.commands:
                    cmd_summary = ", ".join([cmd.get('type', 'unknown') for cmd in msg.commands])
                    summary_parts.append(f"Assistant: {msg.content} (Executed: {cmd_summary})")
                else:
                    summary_parts.append(f"Assistant: {msg.content}")
            elif msg.role == 'job' and msg.job_info:
                status = msg.job_info.get('job_status', 'unknown')
                progress = msg.job_info.get('job_progress', 0)
                if msg.job_info.get('image_url'):
                    summary_parts.append(f"Job {msg.job_id}: {status} ({progress}%) - Screenshot available")
                else:
                    summary_parts.append(f"Job {msg.job_id}: {status} ({progress}%)")
        
        return "\n".join(summary_parts)
    
    def get_scene_summary(self) -> str:
        """Get a summary of current scene state for AI context."""
        summary_parts = []
        
        if self.scene_state.lights:
            light_names = [light.name for light in self.scene_state.lights]
            summary_parts.append(f"MM Control Lights: {', '.join(light_names)}")
        
        if self.scene_state.cesium_location:
            lat = self.scene_state.cesium_location.get('latitude')
            lng = self.scene_state.cesium_location.get('longitude') 
            summary_parts.append(f"Cesium Location: {lat}, {lng}")
        
        if self.scene_state.sky_settings:
            sky_info = []
            if 'time_of_day' in self.scene_state.sky_settings:
                sky_info.append(f"Time: {self.scene_state.sky_settings['time_of_day']}")
            if 'color_temperature' in self.scene_state.sky_settings:
                sky_info.append(f"Color Temp: {self.scene_state.sky_settings['color_temperature']}")
            if sky_info:
                summary_parts.append(f"Sky Settings: {', '.join(sky_info)}")
        
        return "\n".join(summary_parts) if summary_parts else "No scene state tracked yet."
    
    def set_llm_model(self, model: str):
        """Set the user's preferred model for this session."""
        self.llm_model = model
        self.last_accessed = datetime.now()
    
    def get_llm_model(self) -> str:
        """Get the user's preferred model for this session."""
        return self.llm_model
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'conversation_history': [msg.to_dict() for msg in self.conversation_history],
            'scene_state': self.scene_state.to_dict(),
            'user_preferences': self.user_preferences,
            'metadata': self.metadata,
            'session_name': self.session_name,
            'llm_model': self.llm_model
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionContext':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            session_id=data['session_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_accessed=datetime.fromisoformat(data['last_accessed']),
            conversation_history=[ChatMessage.from_dict(msg) for msg in data.get('conversation_history', [])],
            scene_state=SceneState.from_dict(data.get('scene_state', {})),
            user_preferences=data.get('user_preferences', {}),
            metadata=data.get('metadata', {}),
            session_name=data.get('session_name'),
            llm_model=data.get('llm_model', 'gemini-2')
        )