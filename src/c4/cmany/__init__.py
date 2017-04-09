#__import__('pkg_resources').declare_namespace(__name__)

from .conf import *

from .build_flags import BuildFlags as BuildFlags
from .system import System as System
from .architecture import Architecture as Architecture
from .compiler import Compiler as Compiler
from .build_type import BuildType as BuildType
from .variant import Variant as Variant
from .build import Build as Build
from .project import Project as Project
