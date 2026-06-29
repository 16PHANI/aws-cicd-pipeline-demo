# Deliberately not using the AWS ruleset plugin here. Pinning a third-party
# plugin version that I can't verify against the actual plugin registry
# from this environment is how you end up with a CI job that fails on day
# one for reasons that have nothing to do with the Terraform code itself.
# Core rules below need no plugin download, so this is the same on every
# machine and every CI run, before and after a plugin release ships.

rule "terraform_unused_declarations" {
  enabled = true
}

rule "terraform_naming_convention" {
  enabled = true
}

rule "terraform_deprecated_interpolation" {
  enabled = true
}

rule "terraform_documented_variables" {
  enabled = false
}
