"""Base class for dossier sections.

This module provides the abstract base class that all dossier section generators
must inherit from. It defines the interface for generating markdown content.
"""

from abc import ABC, abstractmethod
from typing import List


class DossierSection(ABC):
    """Abstract base class for dossier sections.
    
    All dossier section generators must inherit from this class and implement
    the generate() method. Each section is responsible for generating its own
    markdown content as a list of strings (lines).
    
    The section-based architecture allows for:
    - Independent testing of each section
    - Easy modification of individual sections without affecting others
    - Clear separation of concerns in dossier generation
    - Reusable section components
    """
    
    @abstractmethod
    def generate(self) -> List[str]:
        """Generate section content as list of markdown lines.
        
        This method must be implemented by all concrete section classes.
        Each implementation should return a list of strings representing
        the markdown lines for that section, including any headers,
        content, and formatting.
        
        Returns:
            List[str]: List of markdown lines for this section.
                      Each string represents one line of the output.
                      Lines should NOT include trailing newlines.
        
        Example:
            >>> section = ConcreteSection(data)
            >>> lines = section.generate()
            >>> lines
            ['', '## SECTION 1: TITLE', 'Content line 1', 'Content line 2']
        """
        pass
