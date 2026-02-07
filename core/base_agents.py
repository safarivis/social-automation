"""
Base Agent Classes for Multi-Platform Social Automation

Provides configurable base classes that load prompts from YAML files.
"""
from typing import Optional, Dict, Any, List
from pathlib import Path
from agno.agent import Agent
from agno.models.xai import xAI
from agno.db.sqlite import SqliteDb
from pydantic import BaseModel
import yaml


class PromptLoader:
    """Loads and renders prompt templates from YAML files"""

    def __init__(self, prompts_dir: Optional[Path] = None):
        self.prompts_dir = prompts_dir or Path(__file__).parent.parent / "config" / "prompts"
        self._cache: Dict[str, Dict] = {}

    def load_template(self, category: str, template_name: str) -> Dict[str, Any]:
        """
        Load a prompt template from YAML file.

        Args:
            category: Prompt category (research, content)
            template_name: Template file name (without .yaml)

        Returns:
            Parsed YAML as dictionary
        """
        cache_key = f"{category}/{template_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        template_path = self.prompts_dir / category / f"{template_name}.yaml"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, 'r') as f:
            template = yaml.safe_load(f)

        self._cache[cache_key] = template
        return template

    def render_prompt(
        self,
        category: str,
        template_name: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Load a template and render it with variables.

        Args:
            category: Prompt category
            template_name: Template file name
            variables: Variables to substitute in template

        Returns:
            Rendered prompt string
        """
        template = self.load_template(category, template_name)
        base_prompt = template.get("base_prompt", "")

        # Simple variable substitution using format
        try:
            rendered = base_prompt.format(**variables)
        except KeyError as e:
            # If variable missing, leave placeholder
            rendered = base_prompt
            for key, value in variables.items():
                rendered = rendered.replace(f"{{{key}}}", str(value))

        return rendered

    def get_niche_config(
        self,
        category: str,
        template_name: str,
        niche: str
    ) -> Dict[str, Any]:
        """
        Get niche-specific configuration from a template.

        Args:
            category: Prompt category
            template_name: Template file name
            niche: Niche identifier

        Returns:
            Niche configuration dictionary
        """
        template = self.load_template(category, template_name)
        niches = template.get("niches", {})
        return niches.get(niche, {})


# Global prompt loader instance
prompt_loader = PromptLoader()


def create_agent(
    name: str,
    model_id: str,
    db_file: Path,
    instructions: str,
    tools: Optional[List] = None,
    output_schema: Optional[type] = None,
    learning: bool = True,
    **kwargs
) -> Agent:
    """
    Factory function to create a configured Agno agent.

    Args:
        name: Agent name
        model_id: Grok model ID
        db_file: Path to SQLite database
        instructions: Agent instructions
        tools: Optional list of tools
        output_schema: Optional Pydantic output schema
        learning: Enable learning mode
        **kwargs: Additional agent kwargs

    Returns:
        Configured Agent instance
    """
    return Agent(
        name=name,
        model=xAI(id=model_id),
        db=SqliteDb(db_file=str(db_file)),
        learning=learning,
        instructions=instructions,
        tools=tools or [],
        output_schema=output_schema,
        add_datetime_to_context=True,
        markdown=True,
        **kwargs
    )


class ConfigurableAgent:
    """
    A wrapper that creates agents with configurable prompts loaded from YAML.

    This allows changing agent behavior by editing YAML files without
    modifying Python code.
    """

    def __init__(
        self,
        name: str,
        prompt_category: str,
        prompt_template: str,
        model_id: str,
        db_file: Path,
        tools: Optional[List] = None,
        output_schema: Optional[type] = None,
        base_instructions: str = "",
        learning: bool = True,
    ):
        self.name = name
        self.prompt_category = prompt_category
        self.prompt_template = prompt_template
        self.model_id = model_id
        self.db_file = db_file
        self.tools = tools or []
        self.output_schema = output_schema
        self.base_instructions = base_instructions
        self.learning = learning
        self._agent: Optional[Agent] = None

    def load_instructions(self, variables: Optional[Dict[str, Any]] = None) -> str:
        """Load and render instructions from YAML template"""
        try:
            template = prompt_loader.load_template(
                self.prompt_category,
                self.prompt_template
            )
            instructions = template.get("instructions", template.get("base_prompt", ""))

            # Render with variables if provided
            if variables:
                for key, value in variables.items():
                    instructions = instructions.replace(f"{{{key}}}", str(value))

            # Prepend base instructions if any
            if self.base_instructions:
                instructions = f"{self.base_instructions}\n\n{instructions}"

            return instructions
        except FileNotFoundError:
            # Fall back to base instructions
            return self.base_instructions

    def get_agent(self, variables: Optional[Dict[str, Any]] = None) -> Agent:
        """Get or create the underlying Agno agent"""
        if self._agent is None or variables:
            instructions = self.load_instructions(variables)
            self._agent = create_agent(
                name=self.name,
                model_id=self.model_id,
                db_file=self.db_file,
                instructions=instructions,
                tools=self.tools,
                output_schema=self.output_schema,
                learning=self.learning,
            )
        return self._agent

    def run(self, message: str, variables: Optional[Dict[str, Any]] = None, **kwargs):
        """Run the agent with a message"""
        agent = self.get_agent(variables)
        return agent.run(message, **kwargs)

    def print_response(self, message: str, variables: Optional[Dict[str, Any]] = None, **kwargs):
        """Run agent and print streaming response"""
        agent = self.get_agent(variables)
        return agent.print_response(message, **kwargs)
