"""
Label Studio API模块
提供与Label Studio交互的各种工具和类
"""

from .label_studio_client import label_studio_client
from .task import create_tasks
from .labels import LabelStudioXMLGenerator
from .annotator import Annotator, AnnotationGenerator, AnnotateToCreate, AnnotateToAdd, AnnotateToDelete

__all__ = [
    'label_studio_client',
    'create_tasks',
    'LabelStudioXMLGenerator',
    'Annotator',
    'AnnotationGenerator',
    'AnnotateToCreate',
    'AnnotateToAdd',
    'AnnotateToDelete',

]
