"""Badge generation for compliance health scores."""

from datetime import datetime
from urllib.parse import quote
from uuid import UUID

from app.services.health_score.models import (
    Badge,
    BadgeConfig,
    BadgeStyle,
    HealthScore,
    ScoreGrade,
    score_to_color,
)


class BadgeGenerator:
    """Generates compliance badges in various formats."""
    
    # SVG template for shields.io-style badges
    SVG_TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="20" role="img" aria-label="{label}: {message}">
  <title>{label}: {message}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#{label_color}"/>
    <rect x="{label_width}" width="{message_width}" height="20" fill="{message_color}"/>
    <rect width="{width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
    <text aria-hidden="true" x="{label_x}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{label_text_length}">{label}</text>
    <text x="{label_x}" y="140" transform="scale(.1)" fill="#fff" textLength="{label_text_length}">{label}</text>
    <text aria-hidden="true" x="{message_x}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{message_text_length}">{message}</text>
    <text x="{message_x}" y="140" transform="scale(.1)" fill="#fff" textLength="{message_text_length}">{message}</text>
  </g>
</svg>'''
    
    # Color mappings
    COLORS = {
        "brightgreen": "#4c1",
        "green": "#97ca00",
        "yellow": "#dfb317",
        "orange": "#fe7d37",
        "red": "#e05d44",
        "blue": "#007ec6",
        "grey": "#555",
        "lightgrey": "#9f9f9f",
    }
    
    def __init__(self, base_url: str = "https://api.complianceagent.io"):
        self.base_url = base_url
    
    def generate_badge(
        self,
        score: HealthScore,
        config: BadgeConfig | None = None,
    ) -> Badge:
        """Generate a compliance badge for the given score."""
        if config is None:
            config = BadgeConfig(repository_id=score.repository_id)
        
        # Determine badge message
        message = self._format_message(score, config)
        
        # Generate SVG
        svg = self._render_svg(
            label=config.label,
            message=message,
            label_color=config.label_color,
            message_color=score_to_color(score.overall_score),
            style=config.style,
            custom_colors=config.custom_colors,
        )
        
        # Generate URLs
        badge_url = self._build_badge_url(score.repository_id, config)
        
        return Badge(
            repository_id=score.repository_id,
            score=score.overall_score,
            grade=score.grade,
            svg_content=svg,
            url=badge_url,
            markdown=f"[![Compliance]({badge_url})]({self.base_url}/repos/{score.repository_id})",
            html=f'<a href="{self.base_url}/repos/{score.repository_id}"><img src="{badge_url}" alt="Compliance Badge" /></a>',
            generated_at=datetime.utcnow(),
        )
    
    def _format_message(
        self,
        score: HealthScore,
        config: BadgeConfig,
    ) -> str:
        """Format the badge message."""
        parts = []
        
        if config.show_grade:
            parts.append(score.grade.value)
        
        if config.show_score:
            parts.append(f"{score.overall_score:.0f}%")
        
        if not parts:
            parts.append(score.grade.value)
        
        return " ".join(parts)
    
    def _render_svg(
        self,
        label: str,
        message: str,
        label_color: str,
        message_color: str,
        style: BadgeStyle,
        custom_colors: dict[str, str] | None = None,
    ) -> str:
        """Render SVG badge."""
        # Resolve colors
        resolved_label_color = custom_colors.get("label", label_color) if custom_colors else label_color
        resolved_message_color = custom_colors.get("message") if custom_colors else None
        
        if resolved_message_color is None:
            resolved_message_color = self.COLORS.get(message_color, message_color)
        else:
            resolved_message_color = self.COLORS.get(resolved_message_color, resolved_message_color)
        
        if not resolved_message_color.startswith("#"):
            resolved_message_color = f"#{resolved_message_color}"
        
        # Calculate dimensions
        label_text_length = len(label) * 60
        message_text_length = len(message) * 65
        
        label_width = (label_text_length / 10) + 10
        message_width = (message_text_length / 10) + 10
        
        total_width = label_width + message_width
        
        label_x = (label_width / 2) * 10
        message_x = (label_width + message_width / 2) * 10
        
        return self.SVG_TEMPLATE.format(
            width=int(total_width),
            label=label,
            message=message,
            label_width=int(label_width),
            message_width=int(message_width),
            label_color=resolved_label_color,
            message_color=resolved_message_color,
            label_x=int(label_x),
            message_x=int(message_x),
            label_text_length=label_text_length,
            message_text_length=message_text_length,
        )
    
    def _build_badge_url(
        self,
        repository_id: UUID,
        config: BadgeConfig,
    ) -> str:
        """Build badge endpoint URL."""
        params = []
        
        if config.style != BadgeStyle.FLAT:
            params.append(f"style={config.style.value}")
        
        if not config.show_grade:
            params.append("grade=false")
        
        if not config.show_score:
            params.append("score=false")
        
        if config.label != "compliance":
            params.append(f"label={quote(config.label)}")
        
        if config.include_regulations:
            params.append(f"regulations={','.join(config.include_regulations)}")
        
        url = f"{self.base_url}/v1/health-score/{repository_id}/badge.svg"
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    def generate_simple_badge(
        self,
        score: float,
        grade: ScoreGrade,
        label: str = "compliance",
    ) -> str:
        """Generate a simple badge SVG without full config."""
        message = f"{grade.value} {score:.0f}%"
        
        return self._render_svg(
            label=label,
            message=message,
            label_color="555",
            message_color=score_to_color(score),
            style=BadgeStyle.FLAT,
            custom_colors=None,
        )


# Singleton instance
_generator: BadgeGenerator | None = None


def get_badge_generator(base_url: str = "https://api.complianceagent.io") -> BadgeGenerator:
    """Get singleton badge generator."""
    global _generator
    if _generator is None:
        _generator = BadgeGenerator(base_url)
    return _generator
