from enum import Enum
from typing import Optional
import os

from pydantic import BaseModel

from agent.utils import create_memory_if_not_exists

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    role: Role
    content: str


class AgentResponse(BaseModel):
    thoughts: str
    python_block: Optional[str] = None
    reply: Optional[str] = None

    def __str__(self):
        return f"Thoughts: {self.thoughts}\nPython block:\n {self.python_block}\nReply: {self.reply}"
    
class EntityFile(BaseModel):
    entity_name: str
    entity_file_path: str
    entity_file_content: str

class StaticMemory(BaseModel):
    memory_id: str
    user_md: str
    entities: list[EntityFile]

    class Config:
        # This allows the class to work with both v1 and v2
        pass

    def instantiate(self, path: str):
        """
        Instantiate the static memory inside the memory path.
        """
        try:
            # Add memory_id to the path
            path = os.path.join(path, self.memory_id)
            
            # Create the base memory directory
            create_memory_if_not_exists(path)
            
            # Write user.md file
            user_md_path = os.path.join(path, "user.md")
            with open(user_md_path, "w") as f:
                f.write(self.user_md)
            
            # Write entity files
            for entity in self.entities:
                entity_file_path = os.path.join(path, entity.entity_file_path)
                
                # Ensure parent directory exists
                entity_dir = os.path.dirname(entity_file_path)
                if entity_dir and not os.path.exists(entity_dir):
                    os.makedirs(entity_dir, exist_ok=True)
                
                # Write the entity file
                with open(entity_file_path, "w") as f:
                    f.write(entity.entity_file_content)
                    
        except Exception as e:
            print(f"Error instantiating static memory at {path}: {e}")
            raise

    def reset(self, path: str):
        """
        Reset the static memory inside the memory path.
        """
        try:
            # Check if user.md exists and remove it
            user_md_path = os.path.join(path, "user.md")
            if os.path.exists(user_md_path):
                try:
                    os.remove(user_md_path)
                except Exception as e:
                    print(f"Warning: Could not remove {user_md_path}: {e}")
            
            # Remove all entity files based on their paths
            for entity in self.entities:
                entity_file_path = os.path.join(path, entity.entity_file_path)
                if os.path.exists(entity_file_path):
                    try:
                        os.remove(entity_file_path)
                    except Exception as e:
                        print(f"Warning: Could not remove {entity_file_path}: {e}")
                
                # Try to remove parent directories if they're empty
                entity_dir = os.path.dirname(entity_file_path)
                while entity_dir and entity_dir != path:
                    try:
                        if os.path.exists(entity_dir) and not os.listdir(entity_dir):
                            os.rmdir(entity_dir)
                        entity_dir = os.path.dirname(entity_dir)
                    except Exception:
                        # Directory not empty or other error, stop trying
                        break

            # Call the instantiate method
            self.instantiate(path)
        except Exception as e:
            print(f"Error resetting static memory at {path}: {e}")
            raise