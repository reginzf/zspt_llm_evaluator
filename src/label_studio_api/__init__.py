"""
Label Studio API模块
提供与Label Studio交互的各种工具和类
"""

from .label_studio_client import LabelStudioLogin
from .task import create_tasks
from .labels import LabelStudioXMLGenerator
from .annotator import Annotator, AnnotationGenerator, AnnotateToCreate, AnnotateToAdd, AnnotateToDelete

__all__ = [
    'LabelStudioLogin',
    'create_tasks',
    'LabelStudioXMLGenerator',
    'Annotator',
    'AnnotationGenerator',
    'AnnotateToCreate',
    'AnnotateToAdd',
    'AnnotateToDelete',

]
