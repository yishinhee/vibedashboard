"""
파서 레지스트리 — ``sync_service`` 가 ``PARSER_REGISTRY[filename]`` 으로 조회한다.

호출 권장 순서: design → improvement → feature → structure → feature_map
(improvement 가 ChecklistItem 을 만들 때 Phase 가 이미 있어야 stub 생성을 피할 수 있다.)
"""
from apps.parsers.services.base_parser import BaseParser
from apps.parsers.services.design_parser import DesignParser
from apps.parsers.services.feature_map_parser import FeatureMapParser
from apps.parsers.services.feature_parser import FeatureParser
from apps.parsers.services.improvement_parser import ImprovementParser
from apps.parsers.services.structure_parser import StructureParser

PARSER_REGISTRY: dict[str, type[BaseParser]] = {
    "프로젝트설계.md": DesignParser,
    "uiux개선.md": ImprovementParser,
    "기능정의.md": FeatureParser,
    "프로그램구조.md": StructureParser,
    "feature_map.md": FeatureMapParser,
}

__all__ = [
    "BaseParser",
    "PARSER_REGISTRY",
    "FeatureParser",
    "StructureParser",
    "ImprovementParser",
    "DesignParser",
    "FeatureMapParser",
]
