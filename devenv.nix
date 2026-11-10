{ pkgs, ... }:
{
  packages = [
    pkgs.claude-code
    pkgs.uv
    pkgs.python3
    pkgs.zizmor
  ];

  env.UV_PYTHON_DOWNLOADS = "never";

  scripts = {
    validate = {
      description = "Validate the marketplace and every plugin it registers";
      exec = ''cd "$DEVENV_ROOT" && claude plugin validate . --strict'';
    };
    validate-manifests = {
      description = "Validate the manifests against the published JSON Schemas";
      exec = ''cd "$DEVENV_ROOT" && uv run plugins/upskill/skills/upskill/scripts/validate_manifests.py .'';
    };
    validate-skills = {
      description = "Validate every SKILL.md against the Agent Skills format rules";
      exec = ''
        set -eu
        cd "$DEVENV_ROOT"
        skills=$(find plugins -mindepth 3 -maxdepth 3 -type d -path 'plugins/*/skills/*' | sort)
        if [ -z "$skills" ]; then
          echo "no skills found under plugins/*/skills/" >&2
          exit 1
        fi
        # shellcheck disable=SC2086
        uv run plugins/upskill/skills/upskill/scripts/validate_skill.py $skills
      '';
    };
    audit-workflows = {
      description = "Audit the GitHub Actions workflows for security issues";
      exec = ''cd "$DEVENV_ROOT" && zizmor .github/workflows/'';
    };
  };

  enterTest = ''
    validate
    validate-manifests
    validate-skills
  '';
}
