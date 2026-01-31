"""Control Mapping - Maps controls across compliance frameworks."""

from typing import Any

import structlog

from app.services.evidence.models import ControlMapping, Framework


logger = structlog.get_logger()


# Cross-framework control mappings
CONTROL_MAPPINGS: list[ControlMapping] = [
    # SOC2 <-> ISO27001
    ControlMapping(
        source_framework=Framework.SOC2,
        source_control_id="CC6.1",
        target_framework=Framework.ISO27001,
        target_control_id="A.9.1",
        mapping_type="equivalent",
        notes="Both address logical access security",
    ),
    ControlMapping(
        source_framework=Framework.SOC2,
        source_control_id="CC7.1",
        target_framework=Framework.ISO27001,
        target_control_id="A.12.4",
        mapping_type="partial",
        notes="SOC2 CC7.1 maps partially to ISO27001 logging requirements",
    ),
    ControlMapping(
        source_framework=Framework.SOC2,
        source_control_id="CC8.1",
        target_framework=Framework.ISO27001,
        target_control_id="A.12.1.2",
        mapping_type="equivalent",
        notes="Both address change management",
    ),
    
    # SOC2 <-> HIPAA
    ControlMapping(
        source_framework=Framework.SOC2,
        source_control_id="CC6.1",
        target_framework=Framework.HIPAA,
        target_control_id="164.312(a)(1)",
        mapping_type="partial",
        notes="Both address access controls",
    ),
    ControlMapping(
        source_framework=Framework.SOC2,
        source_control_id="CC7.1",
        target_framework=Framework.HIPAA,
        target_control_id="164.312(b)",
        mapping_type="partial",
        notes="Both address audit controls and monitoring",
    ),
    
    # ISO27001 <-> HIPAA
    ControlMapping(
        source_framework=Framework.ISO27001,
        source_control_id="A.9.1",
        target_framework=Framework.HIPAA,
        target_control_id="164.312(a)(1)",
        mapping_type="partial",
        notes="Both address access control requirements",
    ),
    
    # SOC2 <-> GDPR
    ControlMapping(
        source_framework=Framework.SOC2,
        source_control_id="CC6.1",
        target_framework=Framework.GDPR,
        target_control_id="Art.32",
        mapping_type="partial",
        notes="Access controls support GDPR security requirements",
    ),
    
    # PCI-DSS <-> SOC2
    ControlMapping(
        source_framework=Framework.PCI_DSS,
        source_control_id="8.1",
        target_framework=Framework.SOC2,
        target_control_id="CC6.1",
        mapping_type="partial",
        notes="Both address user identification and access",
    ),
    ControlMapping(
        source_framework=Framework.PCI_DSS,
        source_control_id="3.4",
        target_framework=Framework.SOC2,
        target_control_id="CC6.7",
        mapping_type="partial",
        notes="Both address data encryption",
    ),
    
    # ISO27001 <-> GDPR
    ControlMapping(
        source_framework=Framework.ISO27001,
        source_control_id="A.5.1",
        target_framework=Framework.GDPR,
        target_control_id="Art.32",
        mapping_type="related",
        notes="Security policies support GDPR security measures",
    ),
    ControlMapping(
        source_framework=Framework.ISO27001,
        source_control_id="A.18.1",
        target_framework=Framework.GDPR,
        target_control_id="Art.5",
        mapping_type="related",
        notes="Legal compliance controls relate to GDPR principles",
    ),
]


class ControlMapper:
    """Maps controls across compliance frameworks."""

    def __init__(self):
        self._mappings = CONTROL_MAPPINGS
        self._index = self._build_index()

    def _build_index(self) -> dict[str, list[ControlMapping]]:
        """Build lookup index for mappings."""
        index = {}
        for mapping in self._mappings:
            key = f"{mapping.source_framework.value}:{mapping.source_control_id}"
            if key not in index:
                index[key] = []
            index[key].append(mapping)
        return index

    def get_mappings(
        self,
        framework: Framework,
        control_id: str,
    ) -> list[ControlMapping]:
        """Get all mappings for a control."""
        key = f"{framework.value}:{control_id}"
        direct = self._index.get(key, [])
        
        # Also check reverse mappings
        reverse = []
        for mapping in self._mappings:
            if (mapping.target_framework == framework and
                mapping.target_control_id == control_id):
                reverse.append(ControlMapping(
                    source_framework=mapping.target_framework,
                    source_control_id=mapping.target_control_id,
                    target_framework=mapping.source_framework,
                    target_control_id=mapping.source_control_id,
                    mapping_type=mapping.mapping_type,
                    notes=mapping.notes,
                ))
        
        return direct + reverse

    def get_equivalent_controls(
        self,
        framework: Framework,
        control_id: str,
        target_framework: Framework | None = None,
    ) -> list[dict[str, Any]]:
        """Get equivalent controls in other frameworks."""
        mappings = self.get_mappings(framework, control_id)
        
        results = []
        for mapping in mappings:
            if target_framework and mapping.target_framework != target_framework:
                continue
            
            results.append({
                "framework": mapping.target_framework.value,
                "control_id": mapping.target_control_id,
                "mapping_type": mapping.mapping_type,
                "notes": mapping.notes,
            })
        
        return results

    def calculate_coverage(
        self,
        source_framework: Framework,
        completed_controls: list[str],
        target_framework: Framework,
    ) -> dict[str, Any]:
        """Calculate coverage of target framework based on completed controls.
        
        Args:
            source_framework: Framework where controls are completed
            completed_controls: List of completed control IDs
            target_framework: Framework to calculate coverage for
            
        Returns:
            Coverage analysis
        """
        # Get all target controls (from our mapping data)
        target_controls = set()
        for mapping in self._mappings:
            if mapping.target_framework == target_framework:
                target_controls.add(mapping.target_control_id)
            if mapping.source_framework == target_framework:
                target_controls.add(mapping.source_control_id)
        
        # Find covered controls
        covered_controls = set()
        for control_id in completed_controls:
            mappings = self.get_mappings(source_framework, control_id)
            for mapping in mappings:
                if mapping.target_framework == target_framework:
                    covered_controls.add(mapping.target_control_id)
        
        coverage_pct = (len(covered_controls) / len(target_controls) * 100) if target_controls else 0
        
        return {
            "source_framework": source_framework.value,
            "target_framework": target_framework.value,
            "completed_source_controls": len(completed_controls),
            "target_controls_total": len(target_controls),
            "target_controls_covered": len(covered_controls),
            "coverage_percentage": round(coverage_pct, 2),
            "covered_controls": list(covered_controls),
            "uncovered_controls": list(target_controls - covered_controls),
        }

    def generate_reuse_report(
        self,
        frameworks: list[Framework],
    ) -> dict[str, Any]:
        """Generate a report showing evidence reuse potential across frameworks."""
        reuse_opportunities = []
        
        for mapping in self._mappings:
            if (mapping.source_framework in frameworks and 
                mapping.target_framework in frameworks):
                reuse_opportunities.append({
                    "from_framework": mapping.source_framework.value,
                    "from_control": mapping.source_control_id,
                    "to_framework": mapping.target_framework.value,
                    "to_control": mapping.target_control_id,
                    "mapping_type": mapping.mapping_type,
                    "reuse_potential": "high" if mapping.mapping_type == "equivalent" else "medium",
                })
        
        # Count by mapping type
        type_counts = {}
        for opp in reuse_opportunities:
            mt = opp["mapping_type"]
            type_counts[mt] = type_counts.get(mt, 0) + 1
        
        return {
            "frameworks_analyzed": [f.value for f in frameworks],
            "total_reuse_opportunities": len(reuse_opportunities),
            "by_mapping_type": type_counts,
            "opportunities": reuse_opportunities,
            "estimated_effort_reduction": f"{min(len(reuse_opportunities) * 5, 40)}%",
        }

    def add_mapping(self, mapping: ControlMapping) -> None:
        """Add a new control mapping."""
        self._mappings.append(mapping)
        key = f"{mapping.source_framework.value}:{mapping.source_control_id}"
        if key not in self._index:
            self._index[key] = []
        self._index[key].append(mapping)


# Global instance
_mapper: ControlMapper | None = None


def get_control_mapper() -> ControlMapper:
    """Get or create control mapper."""
    global _mapper
    if _mapper is None:
        _mapper = ControlMapper()
    return _mapper
