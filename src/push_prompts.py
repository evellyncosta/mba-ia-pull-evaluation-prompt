"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
        if not username:
            raise ValueError("USERNAME_LANGSMITH_HUB não configurado no .env")

        repo_name = f"{username}/{prompt_name}"
        description = prompt_data.get("description", "").strip() or f"Prompt {prompt_name}"
        tags = list(prompt_data.get("tags", []))
        techniques = list(prompt_data.get("techniques_applied", []))

        for technique in techniques:
            tag = str(technique).strip()
            if tag and tag not in tags:
                tags.append(tag)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_data["system_prompt"].strip()),
                ("human", prompt_data.get("user_prompt", "{bug_report}").strip()),
            ]
        )

        readme_lines = [
            f"# {prompt_name}",
            "",
            description,
            "",
            f"- Version: {prompt_data.get('version', 'N/A')}",
        ]

        if techniques:
            readme_lines.append(f"- Techniques: {', '.join(map(str, techniques))}")

        if tags:
            readme_lines.append(f"- Tags: {', '.join(map(str, tags))}")

        if prompt_data.get("created_at"):
            readme_lines.append(f"- Created at: {prompt_data['created_at']}")

        url = hub.push(
            repo_name,
            prompt,
            new_repo_is_public=True,
            new_repo_description=description,
            readme="\n".join(readme_lines),
            tags=tags,
        )

        print(f"   ✓ Push concluído: {repo_name}")
        print(f"     URL: {url}")
        return True

    except Exception as e:
        print(f"   ❌ Erro ao fazer push de '{prompt_name}': {e}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    if not isinstance(prompt_data, dict):
        return False, ["Prompt deve ser um objeto YAML"]

    required_fields = ["description", "system_prompt", "version"]
    for field in required_fields:
        value = prompt_data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"Campo obrigatório inválido ou vazio: {field}")

    system_prompt = str(prompt_data.get("system_prompt", "")).strip()
    if "TODO" in system_prompt:
        errors.append("system_prompt ainda contém TODOs")

    user_prompt = prompt_data.get("user_prompt", "{bug_report}")
    if not isinstance(user_prompt, str) or not user_prompt.strip():
        errors.append("user_prompt inválido ou vazio")

    tags = prompt_data.get("tags", [])
    if tags is not None and not isinstance(tags, list):
        errors.append("tags deve ser uma lista")

    techniques = prompt_data.get("techniques_applied", [])
    if techniques is not None and not isinstance(techniques, list):
        errors.append("techniques_applied deve ser uma lista")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS")

    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    prompt_file = "prompts/bug_to_user_story_v2.yml"
    prompt_definitions = load_yaml(prompt_file)

    if not prompt_definitions:
        print(f"❌ Não foi possível carregar prompts de {prompt_file}")
        return 1

    if not isinstance(prompt_definitions, dict):
        print(f"❌ Estrutura inválida em {prompt_file}: esperado objeto no topo do YAML")
        return 1

    print(f"Arquivo carregado: {prompt_file}")
    print(f"Prompts encontrados: {len(prompt_definitions)}\n")

    all_succeeded = True
    pushed_count = 0

    for prompt_name, prompt_data in prompt_definitions.items():
        print(f"Processando prompt: {prompt_name}")

        is_valid, errors = validate_prompt(prompt_data)
        if not is_valid:
            all_succeeded = False
            print("   ❌ Prompt inválido:")
            for error in errors:
                print(f"      - {error}")
            print()
            continue

        if push_prompt_to_langsmith(prompt_name, prompt_data):
            pushed_count += 1
        else:
            all_succeeded = False

        print()

    print("=" * 50)
    print("RESUMO FINAL")
    print("=" * 50)
    print(f"Prompts processados: {len(prompt_definitions)}")
    print(f"Prompts publicados: {pushed_count}")
    print(f"Falhas: {len(prompt_definitions) - pushed_count}")

    if all_succeeded:
        print("\n✅ Todos os prompts foram publicados com sucesso.")
        return 0

    print("\n⚠️  Alguns prompts não foram publicados.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
